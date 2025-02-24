from sentence_transformers import SentenceTransformer, CrossEncoder, util
from torch.nn import Sigmoid
import pandas as pd
from kani.engines.openai import OpenAIEngine
from kani.ai_function import AIFunction
from kani.models import ChatMessage
from kani.engines.openai.translation import ChatCompletion, translate_functions, translate_messages
import os

class RAGEngine(OpenAIEngine):
    def __init__(self, api_key, model, csv_name, top_k=10):
        # Initialize the parent class (OpenAIEngine)
        super().__init__(api_key=api_key, model=model)
        
        # Store additional parameters
        self.top_k = top_k
        self.bi_encoder = SentenceTransformer('all-MiniLM-L12-v2', device='cuda')
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", default_activation_function=Sigmoid())
        self.docs, self.queries, self.query_embeddings = self.load_data(csv_name)

    def load_data(self, csv_name):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, csv_name)

        df_drugs = pd.read_csv(csv_path)
        docs = df_drugs['answers'].tolist()
        queries = df_drugs['questions'].tolist()
        query_embeddings = self.bi_encoder.encode(queries)
        return docs, queries, query_embeddings

    def search(self, query, debug=False):
        # retrieve
        query_embedding = self.bi_encoder.encode(query, convert_to_tensor=True)#.to('cuda')
        hits = util.semantic_search(query_embedding, self.query_embeddings, top_k=self.top_k)[0]

        # rerank
        cross_inp = [[query, self.docs[hit['corpus_id']]] for hit in hits]
        cross_scores = self.cross_encoder.predict(cross_inp)

        # sort by the cross-encoder scores
        for idx in range(len(cross_scores)):
            hits[idx]['cross-score'] = cross_scores[idx]

        if debug:
            # output of retrieval
            print("\n-------------------------\n")
            print("Top-3 Bi-Encoder Retrieval hits")
            hits = sorted(hits, key=lambda x: x['score'], reverse=True)
            for hit in hits[:3]:
                print("\t{:.3f}\t{}".format(hit['score'], self.docs[hit['corpus_id']].replace("\n", " ")))

            # output of rerank
            print("\n-------------------------\n")
            print("Top-3 Cross-Encoder Reranker hits")
            hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)
            for hit in hits[:3]:
                print("\t{:.3f}\t{}".format(hit['cross-score'], self.docs[hit['corpus_id']].replace("\n", " ")))
        else:
            hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)

        # return top 1
        return [(self.queries[hit['corpus_id']], self.docs[hit['corpus_id']]) for hit in hits[:3]]
    
    def rag_prompt(self, question, context):
        prompt = f"""QUESTION TO ANSWER: {question}
            Context for answering the question: {context}
            Answer:"""
        return prompt

    def rag(self, query):
        qa_pairs = self.search(query, need_print=False)
        content = '\n'.join([f"Question: {q} Answer: {a}" for q,a in qa_pairs])
        prompt = self.rag_prompt(query, content)
        return prompt

    async def predict(
        self, messages: list[ChatMessage], functions: list[AIFunction] | None = None, **hyperparams
    ) -> ChatCompletion:
        if functions:
            tool_specs = translate_functions(functions)
        else:
            tool_specs = None
        # translate to openai spec - group any tool messages together and ensure all free ToolCall IDs are bound
        translated_messages = translate_messages(messages)
        translated_messages[-1]['content'] = self.rag(translated_messages[-1]['content'])
        
        # make API call
        completion = await self.client.chat.completions.create(
            model=self.model, messages=translated_messages, tools=tool_specs, **self.hyperparams, **hyperparams
        )
        # translate into Kani spec and return
        kani_cmpl = ChatCompletion(openai_completion=completion)
        self.set_cached_message_len(kani_cmpl.message, kani_cmpl.completion_tokens)
        return kani_cmpl


    
# model = "gpt-4o-mini"
# engine = RAGEngine(api_key=api_key, model=model, csv_name="Substance_Use_and_Recovery_FAQ.csv")
# system_prompt = """you are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, JUST SAY THAT YOU DON'T KNOW. Use 2-3 sentences maximum and keep the answer concise."""
# kani = Kani(engine, system_prompt=system_prompt)
# response = await kani.chat_round(query="Why is age of first use of alcohol so critically important?")
# response.text
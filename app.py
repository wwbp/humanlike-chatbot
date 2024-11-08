import streamlit as st
import asyncio
import pandas as pd
import random
import time
import numpy as np
import shutil  # For zipping directories
from kani import Kani, ai_function, AIParam
from kani.engines.openai import OpenAIEngine
from kani.engines.anthropic import AnthropicEngine
from convokit import Corpus, download
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os

st.title("Enhanced Kani Chatbot Interface with Advanced Features")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
MESSAGE_THRESHOLD = 10  # Save only if messages >= 10

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Sidebar with API key inputs and settings
with st.sidebar:
    st.title("Settings")
    openai_api_key_input = st.text_input(
        "Enter your OpenAI API key:",
        type="password",
        placeholder="sk-...",
        help="Get your OpenAI API key from https://platform.openai.com/account/api-keys",
    )

    anthropic_api_key_input = st.text_input(
        "Enter your Anthropic API key:",
        type="password",
        placeholder="api-key-...",
        help="Get your Anthropic API key from https://console.anthropic.com/account/keys",
    )

    if openai_api_key_input:
        st.session_state["openai_api_key"] = openai_api_key_input

    if anthropic_api_key_input:
        st.session_state["anthropic_api_key"] = anthropic_api_key_input

    style = st.selectbox(
        "Select a style for the assistant:",
        ["Default", "Formal", "Informal", "Humorous", "Happy", "Sad", "Immigrant Accent"]
    )

    persona = st.selectbox(
        "Select a persona for the assistant:",
        ["None", "Formal Assistant", "Casual Friend", "Professional Mentor", "New Immigrant"]
    )

    model_choices = st.multiselect(
        "Select the model(s) to use:",
        ["OpenAI GPT-4o-mini", "Anthropic Claude-2.1"],
        default=["OpenAI GPT-4o-mini"]
    )

    memory_length = st.slider(
        "Memory Length (number of recent exchanges to remember):",
        min_value=2,
        max_value=20,
        value=5,
        step=1,
    )

    st.write("""
    **Memory Length Explanation:**
    Adjusting the memory length changes how many recent exchanges the assistant remembers.
    A shorter memory may cause the assistant to lose context, while a longer memory helps maintain continuity.
    """)

    save_convokit_format = st.checkbox("Save conversation in Convokit format")
    analyze_sentiment = st.checkbox("Analyze sentiment using VADER")

    if st.button("Delete Chat History"):
        if "messages" in st.session_state:
            del st.session_state["messages"]

    start_bot_conversation = st.button("Start Bot-to-Bot Conversation")
    bot_rounds = st.slider("Number of Bot Rounds", min_value=1, max_value=10, value=5)

    load_gap_corpus = st.checkbox("Load and Analyze GAP Corpus")

# Check for API keys
if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
    st.error("Please enter your OpenAI API key in the sidebar.")
    st.stop()
else:
    openai_api_key = st.session_state["openai_api_key"]

if "anthropic_api_key" not in st.session_state or not st.session_state["anthropic_api_key"]:
    st.error("Please enter your Anthropic API key in the sidebar.")
    st.stop()
else:
    anthropic_api_key = st.session_state["anthropic_api_key"]

# Initialize Kani engines
openai_engine = OpenAIEngine(api_key=openai_api_key, model="gpt-4o-mini")
anthropic_engine = AnthropicEngine(api_key=anthropic_api_key, model="claude-2.1")

style_prompts = {
    "Default": "",
    "Formal": "Please communicate in a formal manner.",
    "Informal": "Please communicate informally, using casual language.",
    "Humorous": "Please add humor to your responses.",
    "Happy": "Please respond in a cheerful and upbeat tone.",
    "Sad": "Please respond in a somber and subdued tone.",
    "Immigrant Accent": "Please speak like a new immigrant from [Country]."
}

persona_prompts = {
    "None": "",
    "Formal Assistant": "You are a professional assistant.",
    "Casual Friend": "You are a friendly, casual conversationalist.",
    "Professional Mentor": "You are an experienced mentor giving advice.",
    "New Immigrant": "You are a new immigrant adjusting to a new country."
}

combined_prompt = f"{persona_prompts.get(persona, '')} {style_prompts.get(style, '')}".strip()
if not combined_prompt:
    combined_prompt = "You are a helpful assistant."

# Custom memory class with Convokit memory handling
class MemoryKani(Kani):
    async def get_prompt(self):
        last_messages = self.chat_history[-(memory_length * 2):]
        return self.always_included_messages + last_messages

def sentiment_analysis(text):
    sentiment = analyzer.polarity_scores(text)
    if sentiment["compound"] >= 0.05:
        return "Positive"
    elif sentiment["compound"] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def save_conversation_for_convokit(messages, filename="conversation_corpus"):
    # Only save if we have enough messages
    if len(messages) < MESSAGE_THRESHOLD:
        print(f"Debug: Message count {len(messages)} is below threshold ({MESSAGE_THRESHOLD}). Not saving.")
        return

    print("Debug: Saving conversation as Convokit corpus.")
    utterances = []
    for message in messages:
        sentiment = sentiment_analysis(message["content"]) if analyze_sentiment else "N/A"
        utterance = {
            'id': message.get('id', str(len(utterances) + 1)),
            'speaker': message["role"],
            'text': message["content"],
            'conversation_id': 'conversation_1',
            'reply_to': message.get('reply_to'),
            'timestamp': message.get('timestamp', int(time.time())),
            'meta.sentiment': sentiment,
            'meta.intent': "general",
            'meta.topic': "chat"
        }
        utterances.append(utterance)

    df_utterances = pd.DataFrame(utterances)
    df_speakers = pd.DataFrame({
        'id': df_utterances['speaker'].unique(),
    })
    conversation_df = pd.DataFrame({
        'id': ['conversation_1'],
        'utterances': [df_utterances['id'].tolist()]
    })

    corpus = Corpus.from_pandas(df_utterances, df_speakers, conversation_df)
    os.makedirs("tmp", exist_ok=True)
    
    # Save corpus and create zip file
    corpus.dump(filename, "tmp")
    shutil.make_archive(f"tmp/{filename}", 'zip', f"tmp/{filename}")
    shutil.rmtree(f"tmp/{filename}")  # Clean up the original directory
    
    file_path = f"tmp/{filename}.zip"
    
    # Confirm if zip file exists
    if not os.path.exists(file_path):
        st.error("File could not be created. Check permissions or path.")
        print("Debug: Zip file creation failed.")
        return
    else:
        print(f"Debug: Zip file created at {file_path}")

    # Check download button functionality
    with open(file_path, "rb") as file:
        st.download_button(
            label="Download Conversation in Convokit Format",
            data=file,
            file_name=f"{filename}.zip",
            mime="application/zip"
        )

    st.write("Conversation saved and ready for download.")

async def chat():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for message in st.session_state["messages"]:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    if prompt := st.chat_input("How can I help?"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        for model_choice in model_choices:
            ai_engine = openai_engine if model_choice == "OpenAI GPT-4o-mini" else anthropic_engine
            ai = MemoryKani(ai_engine, system_prompt=combined_prompt)

            with st.chat_message(f"assistant ({model_choice})", avatar=BOT_AVATAR):
                message_placeholder = st.empty()
                full_response = ""

                try:
                    response = await ai.chat_round(prompt)
                    full_response = response.text
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    st.error(f"An error occurred with {model_choice}: {e}")
                    full_response = "I'm sorry, but I couldn't process your request."

                st.session_state["messages"].append({
                    "role": f"assistant ({model_choice})",
                    "content": full_response
                })

        if save_convokit_format:
            save_conversation_for_convokit(st.session_state["messages"])

async def bot_conversation():
    openai_bot = MemoryKani(
        openai_engine,
        system_prompt="You are Dr. Bot, a doctor. Start a conversation with the patient."
    )
    anthropic_bot = MemoryKani(
        anthropic_engine,
        system_prompt="You are a patient. Respond to the doctor's questions."
    )
    message = "Hello, I am Dr. Bot. How are you feeling today?"
    chat_history = []

    for idx in range(bot_rounds):
        timestamp = int(time.time())
        response_openai = await openai_bot.chat_round(message)
        chat_history.append({
            'id': str(len(chat_history) + 1),
            'speaker': "Dr. Bot",
            'text': response_openai.text,
            'conversation_id': 'conversation_1',
            'reply_to': chat_history[-1]['id'] if chat_history else None,
            'timestamp': timestamp,
            'meta.sentiment': sentiment_analysis(response_openai.text) if analyze_sentiment else "N/A",
            'meta.intent': "general",
            'meta.topic': "chat"
        })
        st.write(f"**Dr. Bot**: {response_openai.text}")

        # Debug: Print chat_history after each round
        print("Debug: Chat history after Dr. Bot's response:")
        print(chat_history)

        # Patient's turn
        timestamp = int(time.time())
        response_anthropic = await anthropic_bot.chat_round(response_openai.text)
        chat_history.append({
            'id': str(len(chat_history) + 1),
            'speaker': "Patient",
            'text': response_anthropic.text,
            'conversation_id': 'conversation_1',
            'reply_to': chat_history[-1]['id'],
            'timestamp': timestamp,
            'meta.sentiment': sentiment_analysis(response_anthropic.text) if analyze_sentiment else "N/A",
            'meta.intent': "general",
            'meta.topic': "chat"
        })
        st.write(f"**Patient**: {response_anthropic.text}")
        message = response_anthropic.text

    # Verify `chat_history` contents before saving
    print("Debug: Final chat history before saving:")
    print(chat_history)

    if save_convokit_format:
        filename = "bot_conversation_corpus"
        df_utterances = pd.DataFrame(chat_history)
        df_speakers = pd.DataFrame({
            'id': df_utterances['speaker'].unique(),
        })
        conversation_df = pd.DataFrame({
            'id': ['conversation_1'],
            'utterances': [df_utterances['id'].tolist()]
        })

        corpus = Corpus.from_pandas(df_utterances, df_speakers, conversation_df)
        os.makedirs("tmp", exist_ok=True)
        
        # Save corpus and create zip file
        corpus.dump(filename, "tmp")
        shutil.make_archive(f"tmp/{filename}", 'zip', f"tmp/{filename}")
        shutil.rmtree(f"tmp/{filename}")  # Clean up original directory
        
        file_path = f"tmp/{filename}.zip"
        
        if not os.path.exists(file_path):
            st.error("File could not be created. Check permissions or path.")
            print("Debug: Zip file creation failed.")
            return
        else:
            print(f"Debug: Zip file created at {file_path}")

        # Download functionality
        with open(file_path, "rb") as file:
            st.download_button(
                label="Download Bot Conversation in Convokit Format",
                data=file,
                file_name=f"{filename}.zip",
                mime="application/zip"
            )

        st.write("Bot conversation saved and ready for download.")

def analyze_gap_corpus():
    from convokit import Corpus, download
    gap_corpus = Corpus(filename=download("gap-corpus"))
    st.write("GAP Corpus Summary Statistics:")
    st.write(f"Number of Speakers: {len(gap_corpus.get_speaker_ids())}")
    st.write(f"Number of Utterances: {len(gap_corpus.get_utterance_ids())}")
    sentiments = []
    for utt in gap_corpus.iter_utterances():
        text = utt.text
        sentiment = sentiment_analysis(text)
        sentiments.append({
            'Utterance ID': utt.id,
            'Speaker': utt.speaker.id,
            'Text': text,
            'Sentiment': sentiment
        })
    df_sentiments = pd.DataFrame(sentiments)
    st.write("Sentiment Analysis of GAP Corpus:")
    st.dataframe(df_sentiments)

if load_gap_corpus:
    analyze_gap_corpus()
elif start_bot_conversation:
    asyncio.run(bot_conversation())
else:
    asyncio.run(chat())

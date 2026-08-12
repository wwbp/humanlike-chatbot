AI Models
=========

ChatbotLab supports multiple large language model (LLM) providers. Each bot can
be assigned to a specific model depending on your study needs.

Available Providers
-------------------

- **OpenAI:** GPT-4o, GPT-3.5, GPT-5 (if available)
- **Anthropic:** Claude 3 Opus, Sonnet, Haiku
- **Amazon Bedrock:** Llama 3

Configuration
-------------

Set the provider and model in the ChatbotLab admin panel or environment file:

.. code-block:: bash

   MODEL_PROVIDER=openai
   MODEL_NAME=gpt-4o-mini

Performance & Cost
------------------

- *Smaller models* (e.g., GPT-4o-mini) are faster and cheaper.
- *Larger models* (Claude Opus, GPT-5) provide better fluency but higher latency.

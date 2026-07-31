Conversation Analysis
=====================

Once conversations are collected, ChatbotLab data can be exported and
analyzed with external libraries for linguistic and behavioral research.

The :doc:`convokit` and :doc:`text` tutorials both run on the same
synthetic corpus, in ``conversation_data/``. This corpus contains 19
synthetic person-to-AI conversations, generated with the Anthropic API. Each
"person" speaker is tagged with a PHQ-9 depression score, along with age,
gender, and a persona. No real participants are included; see
``conversation_data/README.md`` for details. The corpus ships in two
formats: a ConvoKit export (``conversation_data/convokit/``) and a
flattened, DLATK-style export (``conversation_data/text/``).

The two tutorials use different toolkits and different methods, ConvoKit's
Fighting Words and the R text package's Supervised Dimension Projection, but
find the same pattern in this corpus. Higher-PHQ-9 participants use more
affect and hedging language, such as ``feel`` and ``just``. Lower-PHQ-9
participants use more upbeat, closing language, such as ``alright`` and
``ok``.

.. toctree::
   :maxdepth: 1

   dlatk
   convokit
   text

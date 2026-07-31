Conversation Analysis
=====================

Once conversations are collected, ChatbotLab data can be exported and
analyzed with external libraries for linguistic and behavioral research.

The :doc:`dlatk`, :doc:`convokit`, and :doc:`text` tutorials all run on the
same synthetic corpus, in ``conversation_data/``. This corpus contains 19
synthetic person-to-AI conversations, generated with the Anthropic API. Each
"person" speaker is tagged with a PHQ-9 depression score, along with age,
gender, and a persona. No real participants are included; see
``conversation_data/README.md`` for details. The corpus ships in three
formats: a ConvoKit export (``conversation_data/convokit/``), a flattened,
DLATK-style export (``conversation_data/text/``), and a SQLite database
built from that export (``conversation_data/dlatk/``).

The three tutorials use three different toolkits and three different
methods: DLATK's frequency correlation, ConvoKit's Fighting Words, and the R
text package's Supervised Dimension Projection. All three find the same
pattern in this corpus. Higher-PHQ-9 participants use more affect and
hedging language, such as ``feel`` and ``just``. Lower-PHQ-9 participants
use more upbeat, closing language, such as ``alright`` and ``ok``.

.. toctree::
   :maxdepth: 1

   dlatk
   convokit
   text

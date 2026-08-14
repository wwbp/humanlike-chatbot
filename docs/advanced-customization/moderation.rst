Content Moderation
==================

Overview
--------

ChatbotLab includes built-in **content moderation** features to detect and manage
inappropriate or harmful content generated during chat sessions. These tools
help protect participants, maintain ethical compliance, and ensure data safety
for research and analysis.

Moderation enables automated screening of both **user messages** and
**model responses**, allowing administrators to prevent unsafe or
noncompliant content from being displayed or recorded.

Moderation Levels
-----------------

ChatbotLab integrates with **model-based moderation APIs** (e.g., OpenAI's
Moderation API) to evaluate each message in real time.

Each message receives:
- **Category scores:** quantitative risk levels (e.g., sexual, violent, hate, harassment)
- **Confidence thresholds:** numerical indicators (0.0-1.0) representing model certainty

Messages exceeding configured thresholds trigger blocking or replacement behavior.

Configuration
-------------

Moderation settings are managed in the ChatbotLab **Admin Panel** under each
**Bot** configuration.

Here, administrators can adjust moderation thresholds for individual
content categories, including:

- ``harassment``
- ``harassment/threatening``
- ``hate``
- ``hate/threatening``
- ``self-harm``
- ``self-harm/instructions``
- ``sexual``
- ``sexual/minors``
- ``violence``
- ``violence/graphic``

.. note::

   Lower thresholds (e.g., 0.1-0.3) create **stricter moderation** and block
   more messages. Setting a threshold to **1.0** effectively disables moderation
   for that category.

Behavior
--------

- **Below threshold:** Message is delivered normally.  
- **Above threshold:** Message is blocked or replaced with a safe fallback.  

Fallback Responses
------------------

When a message is blocked, ChatbotLab automatically replaces it with a neutral
response:

    "Your message could not be processed. Please keep conversations
    respectful and constructive."

Moderation Records
-------------------

When a message is blocked, no call is made to the LLM. Two ``Utterance``
rows are written instead: the participant's message and the fixed warning
reply above.

- ``moderation_category`` is set on **both** rows, so
  ``Utterance.objects.filter(moderation_category__isnull=False)`` returns
  the complete blocked exchange, and the canned warnings can be identified
  (and stripped out of transcripts) without relying on row adjacency or
  matching the warning text.
- ``moderation_scores``, the full category → score map returned by the
  moderation API — including categories that passed, not just the one that
  tripped — is recorded on the **participant's row only**, since that is the
  message it describes.
- The category is never sent to the client. Participants only ever see the
  generic fallback message above.

Both fields are visible, filterable, and read-only in the **Admin Panel**'s
Utterance views — read-only because they record what the moderation path
actually did, not something to hand-edit. CSV export from the Admin Panel
picks up both fields automatically.

Blocks that happened before this tracking existed have no recoverable
category or scores, since the moderation API's response was never stored
for them. Those historical rows are backfilled and labeled ``unknown``
rather than left blank.

Ethical Considerations
----------------------

Moderation thresholds should align with the **Institutional Review Board (IRB)**
or **ethics guidelines** governing your study.

Recommendations:

- Use stricter moderation for vulnerable populations or public-facing studies.
- Document moderation settings in your study protocol.
- Review blocked and flagged messages regularly to ensure no systematic bias.
- When using external moderation APIs, confirm that data transmission complies
  with institutional privacy requirements.


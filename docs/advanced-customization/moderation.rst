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
- **Flagged:** Conversation entry is saved in the database with a moderation flag
  for later review.

Fallback Responses
------------------

When a message is blocked, ChatbotLab automatically replaces it with a neutral
response such as:

> "I'm sorry, I can't discuss that topic."

You can customize fallback responses per bot to maintain tone or study context.

Logging and Review
------------------

All moderated messages are recorded in the database with:

- Message text (if permitted)
- Timestamp
- Category scores
- Flag status (safe / flagged / blocked)

These logs can be accessed through the **Admin Panel** for review and auditing.

Researchers can also export moderation logs alongside other conversation data
for quality control or annotation.

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


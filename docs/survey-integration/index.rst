Survey Integration
==================

Overview
--------

ChatLab integrates directly with major survey platforms like
:doc:`Qualtrics </survey-integration/qualtrics>`, 
:doc:`REDCap </survey-integration/redcap>`, and :doc:`LimeSurvey </survey-integration/limesurvey>`,
allowing you to embed live language model chat sessions within survey instruments. Participants experience the
chatbot as a seamless part of the survey, appearing as an inline question
or form component through an embedded iframe.

This integration enables researchers to collect conversational data
side-by-side with traditional survey responses — making it ideal for
experiments that combine structured and open-ended, human-AI interactions.

Key Features
------------

- **Embedded Conversations:** Add a ChatLab chatbot directly to your survey
  as a question or descriptive block.
- **Automatic Data Linking:** Each conversation session is linked to the
  participant's survey response via shared identifiers (e.g., Qualtrics
  Response ID, REDCap Record ID).
- **Flexible Configuration:** Works across different survey layouts and
  question types, with full support for embedded data fields.
- **Seamless Participant Experience:** Participants interact with the bot
  without leaving the survey environment.

Available Integrations
----------------------

The following guides describe how to embed ChatLab in specific survey
platforms:

.. toctree::
   :maxdepth: 1

   qualtrics
   redcap
   limesurvey


Typical Workflow
----------------

1. **Create or select your ChatLab bot.**  
   Configure prompts, personas, model, and behavioral parameters in the
   ChatLab admin panel.

2. **Deploy ChatLab to your survey platform.**  
   Embed the bot in a **Qualtrics** or **REDCap** survey using the provided
   iframe integration snippet.

3. **Pass participant metadata.**  
   Use survey-specific variables (e.g., ``${e://Field/ResponseID}`` or
   ``[record-id]``) to pass participant and study information to ChatLab
   through URL parameters.

4. **Collect and link data.**  
   ChatLab automatically stores survey IDs, participant IDs, and metadata
   in the backend database for easy merging with survey exports.

Integration Diagram
-------------------

The diagram below shows how ChatLab fits into the survey workflow:

.. code-block:: text

   [Participant]
        │
        ▼
   [Survey Platform]
   (Qualtrics / REDCap /LimeSurvey)
        │  (iframe)
        ▼
       [ChatLab]
        │
        ▼
   [MySQL Database]
        │
        ▼
   [Export & Analysis]

Use Cases
---------

- Embedding realistic AI chat interactions in psychological or behavioral
  studies.
- Testing participant perceptions of AI systems or simulated interviewers.
- Capturing natural language responses for linguistic or affective analysis.
- Running adaptive, conversational survey instruments that vary by response.


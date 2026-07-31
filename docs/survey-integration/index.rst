Survey Integration
==================

Overview
--------

ChatbotLab integrates directly with major survey platforms like
:doc:`Qualtrics </survey-integration/qualtrics>`, 
:doc:`REDCap </survey-integration/redcap>`, and :doc:`LimeSurvey </survey-integration/limesurvey>`,
allowing you to embed live language model chat sessions within survey instruments. The
chatbot appears as part of the survey, as an inline question or form
component through an embedded iframe.

This integration lets researchers collect conversational data side-by-side
with traditional survey responses. It suits experiments that combine
structured and open-ended, human-AI interactions.

Key Features
------------

- **Embedded Conversations:** Add a ChatbotLab chatbot directly to your survey
  as a question or descriptive block.
- **Automatic Data Linking:** Each conversation session is linked to the
  participant's survey response via shared identifiers (e.g., Qualtrics
  Response ID, REDCap Record ID).
- **In-Survey Experience:** Participants interact with the bot without
  leaving the survey environment.

Available Integrations
----------------------

The following guides describe how to embed ChatbotLab in specific survey
platforms:

.. toctree::
   :maxdepth: 1

   qualtrics
   redcap
   limesurvey

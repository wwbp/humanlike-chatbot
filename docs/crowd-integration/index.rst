Crowdworking Integration
========================

Overview
--------

ChatbotLab deploys surveys and chat-based experiments through major
crowdworking platforms such as :doc:`Prolific </crowd-integration/prolific>` and
:doc:`Amazon Mechanical Turk (MTurk) </crowd-integration/mturk>`.
These integrations let you collect naturalistic conversational data
from online participants at scale.

Participants interact with an embedded ChatbotLab bot within your survey
platform (e.g., Qualtrics or REDCap). The survey is then linked to the
crowdworking platform via URL parameters, ensuring that participant metadata
such as worker IDs, session IDs, and study identifiers are automatically
captured and stored in ChatbotLab's backend.

Key Features
------------

- **Unified Data Capture:** All Prolific or MTurk identifiers (e.g.,
  participant ID, study ID, session ID) are automatically logged alongside
  survey and chat data, allowing data merges.

Available Integrations
----------------------

The following guides describe how to configure ChatbotLab with specific
crowdworking platforms:

.. toctree::
   :maxdepth: 1

   prolific
   mturk


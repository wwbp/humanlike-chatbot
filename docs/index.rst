ChatbotLab — Embedding Human-AI Conversations in Research Studies
=================================================================

*An open-source backend for integrating LLM-driven chat experiences into surveys and crowdsourced studies*

Overview
--------

**ChatbotLab** allows researchers to embed large language model (LLM) conversations
directly inside survey platforms such as **Qualtrics**, **REDCap**, and **LimeSurvey**, which can
then be deployed via **Prolific** or **MTurk** for participant recruitment.

Participants never access ChatbotLab directly. Instead, ChatbotLab runs on AWS and
serves a secure web interface that is loaded **within surveys**.
All conversations and metadata are stored automatically for later analysis.

ChatbotLab is designed to run **without programming**. Deployment is a single
automated step, and every part of a study (the model, the prompt, the bot's
behavior) is configured through a web-based admin panel.

Workflow Summary
----------------

1. **Deploy ChatbotLab** on a cloud-based server (Amazon Web Services), using a single automated workflow
2. **Configure your bot** through the admin panel: model, prompt, persona, and conversation behavior
3. **Embed ChatbotLab** within Qualtrics, REDCap, or LimeSurvey
4. **Recruit participants** through Prolific or MTurk
5. **Collect and export conversation data** for analysis

Key Features
------------

- **One-click deployment:** automated, containerized hosting on your own AWS account — no server setup or coding
- **Survey integration:** embed bots inside Qualtrics, REDCap, or LimeSurvey
- **Crowdsourcing integration:** manage participants via Prolific or MTurk
- **Bot configuration:** define prompts, personas, models, and delays through a web admin panel
- **Human-like interaction:** typing delays, message chunking, personas, and idle follow-ups
- **Data collection:** automatically capture conversation and survey metadata, linked per participant
- **Analysis tools:** export to ConvoKit, DLATK, or R's ``text`` for linguistic research

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Deploying ChatbotLab

   deployment/index

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Using ChatbotLab

   survey-integration/index
   crowd-integration/index
   data/index

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Bot Configuration

   llm-integration/index
   humanlike-interaction/index
   advanced-customization/index

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Conversation Analysis

   analysis/index
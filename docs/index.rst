ChatBotLab — Embedding Human-AI Conversations in Research Studies
=================================================================

*An open-source backend for integrating LLM-driven chat experiences into surveys and crowdsourced studies*

Overview
--------

**ChatBotLab** allows researchers to embed large language model (LLM) conversations
directly inside survey platforms such as **Qualtrics**, **REDCap**, and  **LimeSurvey**, which can
then be deployed via **Prolific** or **MTurk** for participant recruitment.

Participants never access ChatLab directly. Instead, ChatLab runs on AWS and
serves a secure web interface that is loaded **within surveys**.
All conversations and metadata are stored automatically for later analysis.

Workflow Summary
----------------

1. **Deploy ChatLab** on a cloud-based server (Amazon Web Services)  
2. **Embed ChatLab** within Qualtrics, REDCap, LimeSurvey  
3. **Run surveys** through Prolific or MTurk for recruitment  
4. **Collect and export conversation data** for analysis  

Key Features
------------

- 🔗 **Survey Integration:** Embed bots inside Qualtrics, REDCap, or LimeSurvey  
- 🤝 **Crowdworking Integration:** Manage participants via Prolific or MTurk  
- ⚙️ **Bot Configuration:** Define prompts, personas, models, and delays  
- 📊 **Data Collection:** Automatically capture conversation metadata  
- 🧠 **Analysis Tools:** Export to DLATK, ConvoKit, or R's `text` for linguistic research  
- 🚀 **AWS Deployment:** Fully containerized, secure cloud hosting  

.. toctree::
   :maxdepth: 2
   :caption: Deploying ChatLab

   deployment/index

.. toctree::
   :maxdepth: 2
   :caption: Using ChatLab

   survey-integration/index
   crowd-integration/index
   data/index

.. toctree::
   :maxdepth: 2
   :caption: Bot Configuration

   llm-integration/index
   humanlike-interaction/index
   advanced-customization/index

.. toctree::
   :maxdepth: 2
   :caption: Developer Documentation

   developer/quickstart
   developer/architecture/index
   api/index
   features/index
   dev-workflow/index
   extending/index

.. toctree::
   :maxdepth: 2
   :caption: Conversation Analysis

   analysis/index

.. toctree::
   :maxdepth: 2
   :caption: Monitoring & Maintenance

   deployment/monitoring

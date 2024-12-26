# GENERIC BOT
## Overview

Generic Bot is a lightweight, modular chatbot framework designed to help researchers deploy and experiment with text-based conversational agents efficiently. Built with a Django backend, a React frontend (in progress), the [Kani]([https://docs.google.com/document/d/1-cyC4nnibAFTxRk5-PV73yGv9hUJpHiCy3lXoQ9WDY0/edit?tab=t.0](https://github.com/zhudotexe/kani)) Framework for LLM integration, and a MariaDB database, it is fully containerized using Docker for seamless deployment.

Researchers can easily customize in config.json file:

- Language model selection
- Anthropomorphism settings
- Bot-specific prompts
- And more to come

The project streamlines research workflow with integration with tools like Qualtrics, and allows efficient data collection and analysis.
For detailed design specifications, see the [link](https://docs.google.com/document/d/1-cyC4nnibAFTxRk5-PV73yGv9hUJpHiCy3lXoQ9WDY0/edit?tab=t.0)

## Directory Structure
---
```
HUMANLIKE-CHATBOT/
├── generic_chatbot/
    ├── generic_chatbot/
    ├── chatbot/
    ├── server/
        ├── engine.py 
    ├── templates/ # Temporary, will move to React FE system
    ├── config.json # Chatbot configuration
    ├── dockerfile.local
    ├── manage.py
    ├── Pipfile
    ├── Pipfile.lock
    ├── wait-for-db.sh
├── docker-compose.yml
├── .env # Replace .env_template with .env and add API keys
├── init.sql
├── README.md
```
---

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Setup

1. Clone the repository under Soojin branch:

    ```bash
    git clone git@github.com:wwbp/humanlike-chatbot.git
    cd humanlike-chatbot
    git checkout Soojin

    ```

2. Build and run the containers for the bot:

    ```bash
    docker-compose -f docker-compose-generic_bot.yml up --build
    ```

3. To stop and remove the volumes:

    ```bash
    docker-compose -f docker-compose-generic_bot.yml down -v
    ```

4. [Optional] Edit the config.json file located at generic_chatbot/config.json to:

- Select a language model.
- Adjust bot-specific settings like anthropomorphism and prompts

---

## Project Status 
Date:26/12/2024

### Current Functionality
- Language model selection and bot/prompt management via config.json
- Chat interaction logging (stored in MariaDB).
- Dockerized for easy setup and deployment.

---

### Known Bugs
- N/A
  
---

### V1 Next Steps
1. Build and integrate the React-based frontend.
2. Implement user ID tracking and storage (consider user-flow for chat page entry).
3. Create a script to convert SQL conversation data to ConvoKit-formatted JSON.
4. Host the project on AWS EC2.
5. Develop comprehensive API documentation for integration.

---

### V2 Future Enhancements
1. Add voice interaction support.
2. Create adaptable UX/UI for various research case

---

## Challenges
- **HuggingFace Support**: Compatibility issues with PyTorch libraries and GPU support in Docker need to be resolved to integrate HuggingFace models.

---

## To Be Specced & Open Questions
- How can user authentication and tracking be best integrated with Qualtrics?

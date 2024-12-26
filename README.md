# GENERIC BOT

## Overview

**GENERIC Bot** is a modular, lightweight chatbot framework working in process for researchers to experiment with and deploy bots for text-based interactions. It supports anthromophism configuration, prompt management, and multi-bot setups, leveraging the **Kani Framework**. The application uses a Django backend, React frontend (in progress), and MariaDB database, all containerized for ease of deployment using Docker.

The project streamlines integration of chatbot in research-cycle (link with qualtrics) and analysis easy for the researchers, for
various projects including but not limited to projects such as palliative care, mental health care and more. 
Check out more detailed design spec: [link](https://docs.google.com/document/d/1-cyC4nnibAFTxRk5-PV73yGv9hUJpHiCy3lXoQ9WDY0/edit?tab=t.0)

## Directory Structure

HUMANLIKE-CHATBOT/
├── generic_chatbot/
    ├── generic_chatbot/
    ├── chatbot/
    ├── server/
        ├── engine.py 
    ├── templates/ # Temporary, will move to React FE system
    ├── config.json # (configure to your need)
    ├── dockerfile.local
    ├── manage.py
    ├── Pipfile
    ├── Pipfile.lock
    ├── wait-for-db.sh
├── docker-compose.yml
├── .env # Replace .env_template with .env and add API keys
├── init.sql
├── README.md


---

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Setup

1. Clone the repository:

    ```bash
    git clone git@github.com:wwbp/humanlike-chatbot.git
    cd humanlike-chatbot
    ```

2. Adjust the `config.json` file (`generic_chatbot/config.json`) to configure your chatbot:
   - Refer to the **Config Settings** section in the [Design Document](https://docs.google.com/document/d/1-cyC4nnibAFTxRk5-PV73yGv9hUJpHiCy3lXoQ9WDY0/edit?tab=t.0) for details.

3. Build and run the containers for the bot:

    ```bash
    docker-compose -f docker-compose-generic_bot.yml up --build
    ```

4. To stop and remove the volumes:

    ```bash
    docker-compose -f docker-compose-generic_bot.yml down -v
    ```

> **Note:** Since the Docker Compose files use default ports, make sure to update the ports if you are testing multiple applications locally.

---

## Current Features
- **Multi-Model Support**: Easily switch between different language models (see `config.json` for details).
- **Prompt Engineering**: Configure prompts for tailored responses.
- **Modular Backend**: Built on Django, allowing for easy customization.
- **Database Integration**: Stores conversation logs using MariaDB.
- **Dockerized Deployment**: Simplifies setup and scalability.
- **Frontend (In Progress)**: Transitioning from Django templates to a React frontend.

---

## Project Status (as of 26th Dec 2024)

### Current Functionality
- Language model selection and management.
- Chat interaction logging (stored in MariaDB).
- Fully Dockerized for easy setup and deployment.

---

### Known Issues
- None at the moment.

---

### V1 Next Steps
1. Build and integrate the React-based frontend.
2. Implement user ID tracking and storage (consider user-flow for chat page entry).
3. Create a script to convert SQL conversation data to ConvoKit-formatted JSON.
4. Host the project on AWS EC2.
5. Develop comprehensive API documentation for integration.

---

### V2 Next Steps
1. Add voice interaction support.
2. Improve UX/UI with iterative design and user feedback.

---

## Challenges
- **HuggingFace Support**: Decide whether to include HuggingFace models. Initial testing revealed issues with PyTorch library installation and GPU usage in Docker.
- **User Authentication**: Consider if users need to log in. Integration with external systems like Qualtrics may simplify user authentication.

---

## Thoughts and Questions
- Should users be required to log in?
- Can user authentication and tracking be streamlined through Qualtrics integration?

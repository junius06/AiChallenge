"""# Telegram OJT Chatbot

## Overview

This Telegram bot is designed for training and information purposes within the CPLABS organization. It offers three main functionalities:

1. **Training**: Provides troubleshooting training by presenting problems and evaluating user solutions.
2. **Retrieving**: Allows users to search for error cases using specific keywords.
3. **Services**: Introduces and provides information about various services offered by CPLABS.

## Features

- **/start**: Displays a welcome message and lists available commands.
- **/training**: Starts a troubleshooting training session.
- **/retrieving**: Allows searching for specific error cases.
- **/services**: Provides information about CPLABS services.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/telegram-ojt-chatbot.git
    cd telegram-ojt-chatbot
    ```

2. **Install required packages**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure your environment**:
    - Rename `config.py.example` to `config.py`.
    - Add your bot token and OpenAI API key in `config.py`.

4. **Run the bot**:
    ```bash
    python bot.py
    ```

## Usage

### /start

Displays a welcome message with instructions on how to use the bot.

### /training

1. **Starts Training**: Begins a session where users solve troubleshooting problems.
2. **User Interaction**: Users submit solutions to the problems presented by the bot.
3. **Evaluation**: The bot evaluates user solutions against expected solutions and provides feedback.

### /retrieving

1. **Start Retrieval**: Prompts users to enter a keyword to search for error cases.
2. **Retrieve Cases**: Searches for error cases matching the keyword and provides the results.

### /services

1. **Start Services**: Shows a list of CPLABS services with buttons for each service.
2. **Service Details**: Provides detailed information about the selected service using ChatGPT.

## File Structure

Main Application
│
├── Start
│   ├── start(update, context)
│   └── LoggerUtility
│
├── ChatGPT
│   ├── request_chat_gpt(prompt)
│   └── API_KEY
│
├── Training
│   ├── __init__(chatgpt, num_problems=3)
│   ├── cancel(update, context)
│   ├── start_training(update, context)
│   ├── present_problem(update, context)
│   ├── handle_user_solution(update, context)
│   └── evaluate_all_solutions(update)
│
├── Retrieving
│   ├── __init__()
│   ├── cancel(update, context)
│   ├── start_retrieving(update, context)
│   └── retrieve_cases(update, context)
│
└── Services
    ├── __init__(chatgpt)
    ├── cancel(update, context)
    ├── start_services(update, context)
    ├── service_handle_callback(update, context)
    └── ChatGPT
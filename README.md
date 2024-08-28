# Telegram OJT Chatbot (Korean)

## 개요

이 텔레그램 봇은 CPLABS 조직 내 교육 및 정보 제공을 목적으로 설계되었습니다. 다음과 같은 주요 기능을 제공합니다:

1. **트레이닝**: 문제를 제시하고 사용자 해결책을 평가하여 문제 해결 능력을 향상시킵니다.
2. **에러 케이스 검색**: 특정 키워드를 사용하여 에러 케이스를 검색할 수 있습니다.
3. **서비스 소개**: CPLABS에서 제공하는 다양한 서비스에 대한 정보를 제공합니다.

## 기능

- **/start**: 환영 메시지를 표시하고 사용 가능한 명령어를 안내합니다.
- **/training**: 트러블슈팅 트레이닝 세션을 시작합니다.
- **/retrieving**: 특정 에러 케이스를 검색할 수 있습니다.
- **/services**: CPLABS의 서비스에 대한 정보를 제공합니다.

## 설치

1. **필요한 패키지 설치**:
    ```bash
    pip install -r requirements.txt
    ```

2. **환경 설정**:
    - `config.py` 파일과 동일한 경로에서 `.env` 파일을 추가하고, 텔레그램 봇 토큰과 OpenAI API 키를 추가합니다.

3. **봇 실행**:
    ```bash
    python3 bot.py
    ```

## 사용 방법

### /start

환영 메시지를 표시하고 봇 사용 방법을 안내합니다.

### /training

1. **트레이닝 시작**: 사용자가 문제를 해결하기 위한 세션을 시작합니다.
2. **사용자 상호작용**: 사용자가 제시된 문제에 대한 해결책을 제출합니다.
3. **평가**: 봇이 사용자 해결책을 예상 해결책과 비교하여 피드백을 제공합니다.

### /retrieving

1. **검색 시작**: 사용자가 키워드를 입력하여 에러 케이스를 검색합니다.
2. **케이스 검색**: 입력된 키워드에 맞는 에러 케이스를 검색하고 결과를 제공합니다.

### /services

1. **서비스 시작**: CPLABS의 서비스 목록을 버튼으로 표시합니다.
2. **서비스 상세**: 선택된 서비스에 대한 자세한 정보를 ChatGPT를 통해 제공합니다.
---
# Telegram OJT Chatbot (English)

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

---
## Code Structure
```text
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
import os
import telebot
from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler
import asyncio
import nest_asyncio
import openai
import random
import json
from utils.logs_utils import LoggerUtility
from config import *

logger_util = LoggerUtility()

# 봇 초기화
bot = telebot.TeleBot(BOT_TOKEN)

# 트러블 슈팅 데이터 저장 및 로드 함수
def save_troubleshooting_data(data):
    with open('troubleshooting_data.json', 'w') as f:
        json.dump(data, f)

def load_troubleshooting_data():
    try:
        with open('troubleshooting_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# 트러블 슈팅 데이터
troubleshooting_data = load_troubleshooting_data()

# ChatGPT API를 사용하여 응답 생성
def generate_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for OJT training."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message['content']

# /start 명령 처리
class Start():
    def __init__(self):
        self.logger_util = LoggerUtility()
        
    async def start(self, update: Update, context) -> None:
        message = (
            "안녕하세요. Hello"
        )
        await self.logger_util.cmd_logs_msg(update)
        await update.message.reply_text(text=message)
        
# def send_welcome(message):
#     bot.reply_to(message, "안녕하세요! 신규자 교육용 OJT 챗봇입니다. /training 명령으로 트러블 슈팅 트레이닝을 시작할 수 있습니다.")

# /training 명령 처리
@bot.message_handler(commands=['training'])
def start_training(message):
    if not troubleshooting_data:
        bot.reply_to(message, "트러블 슈팅 데이터가 없습니다. 먼저 데이터를 추가해주세요.")
        return

    issue = random.choice(troubleshooting_data)
    prompt = f"다음 이슈에 대한 해결 방법을 설명해주세요: {issue['issue']}"
    question = generate_response(prompt)
    
    bot.reply_to(message, f"문제: {question}\n\n답변을 입력해주세요.")
    bot.register_next_step_handler(message, check_answer, issue['solution'])

def check_answer(message, correct_solution):
    user_answer = message.text
    prompt = f"사용자의 답변: {user_answer}\n\n정답: {correct_solution}\n\n사용자의 답변이 정답과 얼마나 일치하는지 평가하고, 개선점을 제시해주세요."
    evaluation = generate_response(prompt)
    bot.reply_to(message, f"평가 결과:\n\n{evaluation}")

# 새로운 트러블 슈팅 데이터 추가
@bot.message_handler(commands=['add_issue'])
def add_issue(message):
    bot.reply_to(message, "새로운 이슈를 입력해주세요.")
    bot.register_next_step_handler(message, process_issue)

def process_issue(message):
    issue = message.text
    bot.reply_to(message, "이슈에 대한 해결 방법을 입력해주세요.")
    bot.register_next_step_handler(message, process_solution, issue)

def process_solution(message, issue):
    solution = message.text
    troubleshooting_data.append({"issue": issue, "solution": solution})
    save_troubleshooting_data(troubleshooting_data)
    bot.reply_to(message, "새로운 트러블 슈팅 데이터가 추가되었습니다.")

# 봇 실행
bot.polling()

# 메인 함수
async def main() -> None:
    # 애플리케이션 빌드
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = Start()
    
    # /start 명령어 핸들러 추가
    application.add_handler(CommandHandler("start", start_handler.start))
    
    # 애플리케이션 실행
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
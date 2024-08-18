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

# /start 명령 처리
class Start():
    def __init__(self):
        self.logger_util = LoggerUtility()
        
    async def start(self, update: Update, context) -> None:
        message = (
            "안녕하세요. 신규자 교육용 OJT 챗봇입니다. 다음 명령을 이용할 수 있습니다:"
            "/training - 트러블 슈팅 트레이닝을 시작할 수 있습니다."
            "/rules - 씨피랩스 사내 규정에 대하여 안내합니다."
            "/services - 씨피랩스에서 운영중인 서비스에 대하여 소개합니다."
            "/quiz - 퀴즈"
        )
        await self.logger_util.cmd_logs_msg(update)
        await update.message.reply_text(text=message)
        
# ChatGPT API를 사용하여 응답 생성
class ChatGPT():
    def __init__(self):
        openai.api_key = API_KEY
        
    @staticmethod
    async def request_chat_gpt(prompt, update: Update):
        user_message = update.message.text
        try: 
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=512, # 256~2048
                temperature=0.4, # 0~1
                messages=[
                    {
                        "role": "system", "content": "You are an expert in server and network troubleshooting.",
                        "role": "user", "content": user_message
                    }
                ]
            )
            # default
            # return response.choices[0].message.content
            
            # OpenAI의 응답 텍스트를 가져오기
            answer = response.choices[0].message['content'].strip()

            # 사용자에게 응답 전송
            await update.message.reply_text(answer)
                    
        except Exception as e:
            return "Sorry, I can't respond at the moment."

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
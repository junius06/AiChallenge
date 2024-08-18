# import os
# import telebot
from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler
import asyncio
import nest_asyncio
# import openai
# import random
# import json
from utils.logs_utils import LoggerUtility
from config import *

logger_util = LoggerUtility()

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
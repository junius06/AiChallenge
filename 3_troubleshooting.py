import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, filters
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
        
# 트러블 슈팅 데이터 로드, 문제 제시 및 평가 클래스
data_files_path = os.path.join(os.path.dirname(__file__), 'troubleshooting_data', 'data.sjon')
with open(data_files_path, "r") as file:
    troubleshooting_data = json.load(file)

class TroubleshootingTraining:
    def __init__(self, chatgpt: ChatGPT):
        self.chatgpt = chatgpt
        self.current_issue = None
        self.current_solution = None

    async def start_training(self, update: Update) -> None:
        # 랜덤 문제 선택
        problem = random.choice(troubleshooting_data)
        self.current_issue = problem["issue"]
        self.current_solution = problem["expected_solution"]

        # 문제 제시
        await update.message.reply_text(f"문제: {self.current_issue}\n문제를 해결하기 위한 방안을 제시하세요.")

    async def evaluate_solution(self, update: Update) -> None:
        user_solution = update.message.text
        prompt = f"Evaluate how close the following user-provided solution is to the expected solution: '{self.current_solution}'.\nUser solution: {user_solution}"
        
        # ChatGPT API를 통해 평가 요청
        evaluation = await self.chatgpt.request_chat_gpt(prompt)

        # 평가 결과 반환
        await update.message.reply_text(f"평가 결과: {evaluation}")

# 메인 함수
async def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    chatgpt = ChatGPT()
    start_handler = Start()
    training_handler = TroubleshootingTraining(chatgpt)
    
    application.add_handler(CommandHandler("start", start_handler.start))
    application.add_handler(CommandHandler("training", training_handler.start_training))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, training_handler.evaluate_solution))

    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
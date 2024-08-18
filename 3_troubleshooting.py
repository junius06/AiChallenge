import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
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
            "안녕하세요. 신규자 교육용 OJT 챗봇입니다. 다음 명령을 이용할 수 있습니다:\n\n"
            "/training - 트러블 슈팅 트레이닝을 시작할 수 있습니다.\n"
            "/rules - 씨피랩스 사내 규정에 대하여 안내합니다.\n"
            "/services - 씨피랩스에서 운영중인 서비스에 대하여 소개합니다.\n"
            "/quiz - 퀴즈"
        )
        await self.logger_util.cmd_logs_msg(update)
        await update.message.reply_text(text=message)
        
# ChatGPT API를 사용하여 응답 생성
class ChatGPT():
    def __init__(self):
        openai.api_key = API_KEY
        
    async def request_chat_gpt(self, prompt: str) -> str:
        try: 
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=512, # 256~2048
                temperature=0.2, # 0~1
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 데브옵스 엔지니어이며 서버와 네트워크에 대한 전문가입니다. 모든 응답을 한국어로 해주세요."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    },
                    {
                        "role": "assistant", 
                        "content": "제 전문 지식을 바탕으로 이 문제를 해결할 수 있는 최선의 해결책을 소개합니다."
                    }
                ]
            )
            return response.choices[0].message['content'].strip()
                    
        except Exception as e:
            return "Sorry, I can't respond at the moment."
        
# 트러블 슈팅 데이터 로드, 문제 제시 및 평가 클래스


class TroubleshootingTraining:
    def __init__(self, chatgpt: ChatGPT):
        self.chatgpt = chatgpt
        self.current_issue = None
        self.current_solution = None
        
        # 트러블슈팅 데이터 로드
        data_files_path = os.path.join(os.path.dirname(__file__), 'troubleshooting_data', 'data.json')
        with open(data_files_path, "r") as file:
            self.troubleshooting_data = json.load(file)

    async def start_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # 랜덤 문제 선택
        problem = random.choice(self.troubleshooting_data)
        self.current_issue = problem["issue"]
        self.current_solution = problem["expected_solution"]

        # 문제 제시
        await update.message.reply_text(f"문제 : {self.current_issue}\n\n문제를 해결하기 위한 방안을 제시하세요.")

    async def evaluate_solution(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_solution = update.message.text
        prompt = f"유저가 제공한 해결책이 예상 해결책에 얼마나 가까운지 평가해주세요. : '{self.current_solution}'.\n사용자 해결책 : {user_solution}"
        
        # ChatGPT API를 통해 평가 요청
        evaluation = await self.chatgpt.request_chat_gpt(prompt)

        # 평가 결과 반환
        await update.message.reply_text(f"평가 결과 : {evaluation}")
        
        # 대화 종료
        return ConversationHandler.END

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
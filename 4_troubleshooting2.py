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

# 상태 정의
PROBLEM_STATE = range(1)

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
                max_tokens=256, # 256~2048
                temperature=0.1, # 0~1
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 데브옵스 엔지니어이며, 서버와 네트워크에 대한 전문가입니다. 한국어로 응답해주세요."
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
    def __init__(self, chatgpt: ChatGPT, num_problems: int = 3):
        self.chatgpt = chatgpt
        self.issues = []
        self.solutions = []
        self.user_solutions = []
        self.num_problems = num_problems
        self.current_problem = 0
        
        # 트러블슈팅 데이터 로드
        data_files_path = os.path.join(os.path.dirname(__file__), 'troubleshooting_data', 'data.json')
        with open(data_files_path, "r") as file:
            self.troubleshooting_data = json.load(file)

    async def start_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.current_problem = 0
        self.issues = []
        self.solutions = []
        self.user_solutions = []
        
        return await self.present_problem(update, context)

    async def present_problem(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if self.current_problem < self.num_problems:
            problem = random.choice(self.troubleshooting_data)
            self.issues.append(problem["issue"])
            self.solutions.append(problem["expected_solution"])
            
            await update.message.reply_text(f"{self.current_problem + 1}번 문제 : {self.issues[self.current_problem]}\n\n문제를 해결하기 위한 방안을 제시하세요.")
            self.current_problem += 1
            return PROBLEM_STATE
        else:
            return await self.evaluate_all_solutions(update)
        
    async def handle_user_solution(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.user_solutions.append(update.message.text)
        return await self.present_problem(update, context)

    async def evaluate_all_solutions(self, update: Update) -> int:
        evaluation_text = ""
        for i in range(self.num_problems):
            prompt = f"유저가 제공한 해결책이 예상 해결책에 얼마나 가까운지 평가해주세요. : '{self.solutions[i]}'.\n사용자 해결책 : {self.user_solutions[i]}"
            evaluation = await self.chatgpt.request_chat_gpt(prompt)
            evaluation_text += f"{i + 1}번 문제 평가 결과: {evaluation}\n\n"
        
        await update.message.reply_text(f"평가 결과 :\n{evaluation_text}")
        return ConversationHandler.END

# 메인 함수
async def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    chatgpt = ChatGPT()
    start_handler = Start()
    training_handler = TroubleshootingTraining(chatgpt, num_problems=10)
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("training", training_handler.start_training)],
        states={
            PROBLEM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, training_handler.handle_user_solution)],
        },
        fallbacks=[],
    )

    application.add_handler(CommandHandler("start", start_handler.start))
    application.add_handler(conv_handler)

    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
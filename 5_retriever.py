import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import nest_asyncio
import openai
import random
import json
from utils.logs_utils import LoggerUtility
from config import *

PROBLEM_STATE = 1
RETRIEVE_STATE = 2

# /start 명령 처리
class Start():
    def __init__(self):
        self.logger_util = LoggerUtility()
        
    async def start(self, update: Update, context) -> None:
        message = (
            "안녕하세요. 신규자 교육용 OJT 챗봇입니다. 다음 명령을 이용할 수 있습니다:\n\n"
            "/retrieve - 특정 키워드로 수집된 에러 케이스를 조회할 수 있습니다.\n"
            "/training - 트러블 슈팅에 대한 트레이닝을 시작할 수 있습니다.\n"
            "/services - 씨피랩스에서 운영중인 서비스에 대하여 소개합니다.\n\n"
            # "<b>CPLABS Bots</b>"
            # "/helpdesk - 씨피랩스 사내 도움을 위한 봇입니다.\n[콩쥐](https://t.me/BeanMouse_securityBot)"
            # "/rules - 씨피랩스 사내 규정 안내를 위한 봇입니다.\n[PEOPLE봇](https://t.me/isms_ss_bot)"
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
        
# 트러블슈팅 문제 제시 및 평가 결과 출력을 위한 트레이닝 클래스
class Training:
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
            
        # 문제 셔플
        self.available_problems = random.sample(self.troubleshooting_data, len(self.troubleshooting_data))
        
    async def cancel_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("트레이닝이 취소되었습니다.")
        return ConversationHandler.END

    async def start_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.current_problem = 0
        self.issues = []
        self.solutions = []
        self.user_solutions = []
        
        return await self.present_problem(update, context)

    async def present_problem(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if self.current_problem < self.num_problems and self.available_problems:
            problem = self.available_problems.pop(0)  # 남은 문제에서 하나를 꺼내서 사용
            self.issues.append(problem["issue"])
            self.solutions.append(problem["expected_solution"])
            
            if self.current_problem == 0:
                await update.message.reply_text(f"총 {self.num_problems}개의 문제가 제공됩니다. 문제를 해결하기 위한 방안을 제시하세요.\n'/cancel' 명령을 입력하여 트레이닝을 종료할 수 있습니다.")
                
            await update.message.reply_text(f"{self.current_problem + 1}번 문제 : {self.issues[self.current_problem]}")
            self.current_problem += 1
            return PROBLEM_STATE
        else:
            return await self.evaluate_all_solutions(update)
        
    async def handle_user_solution(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.user_solutions.append(update.message.text)
        return await self.present_problem(update, context)

    async def evaluate_all_solutions(self, update: Update) -> int:
        evaluation_text = ""
        for i in range(min(len(self.solutions), len(self.user_solutions))):
            prompt = f"유저가 제공한 해결책이 예상 해결책에 얼마나 가까운지 평가해주세요. : '{self.solutions[i]}'.\n사용자 해결책 : {self.user_solutions[i]}"
            evaluation = await self.chatgpt.request_chat_gpt(prompt)
            evaluation_text += f"{i + 1}번 문제 평가 결과: {evaluation}\n\n"
            
        # 리스트 길이 문제 해결
        if len(self.solutions) != len(self.user_solutions):
            evaluation_text += "경고: 예상 해결책과 사용자가 제공한 해결책의 수가 일치하지 않습니다.\n"
        
        await update.message.reply_text(f"평가 결과 :\n{evaluation_text}")
        return ConversationHandler.END

# 에러케이스 검색 클래스
class Retriever:
    def __init__(self):
        self.logger_util = LoggerUtility()
        # 에러 케이스 데이터 로드
        data_files_path = os.path.join(os.path.dirname(__file__), 'troubleshooting_data', 'data.json')
        with open(data_files_path, "r") as file:
            self.error_cases = json.load(file)
            
    def update_user_info(self, update: Update):
        self.user = self.logger_util.user_info_log(update)

    async def start_retrieving(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("조회하고 싶은 에러 케이스의 키워드를 입력하세요.")
        return RETRIEVE_STATE

    async def retrieve_cases(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        keyword = update.message.text.lower()
        context.user_data['keyword'] = keyword
        
        matched_cases = [
            case for case in self.error_cases if re.search(keyword, case['issue'], re.IGNORECASE)
        ]
        
        try:
            self.update_user_info(update)
            
            if matched_cases:
                response = "다음 에러 케이스가 검색되었습니다:\n\n"
                for i, case in enumerate(matched_cases, 1):
                    response += f"task-{i}. {case['issue']}\n\n" # solution. {case['expected_solution']}\n 답변에 대해 원하면 추가함.
            else:
                response = "해당 키워드에 대한 에러 케이스를 찾을 수 없습니다."
                
            log_message = f"The user '{self.user}' searched for error cases by keyword '{keyword}'."
            self.logger_util.log_msg(log_message)
            
            await update.message.reply_text(response)
            
        except Exception as e:
            self.logger_util.logger.error(f'Retriever.retrieve_cases - {e}')
            await update.message.reply_text("오류가 발생했습니다. 다시 시도해주세요.")
        
        return ConversationHandler.END

# 메인 함수
async def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    print('Applicatoin Start.')
    
    chatgpt = ChatGPT()
    start_handler = Start()
    training_handler = Training(chatgpt)
    retriever_handler = Retriever()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("training", training_handler.start_training),
            CommandHandler("retrieve", retriever_handler.start_retrieving)
        ],
        states={
            PROBLEM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, training_handler.handle_user_solution)],
            RETRIEVE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, retriever_handler.retrieve_cases)],
        },
        fallbacks=[CommandHandler("cancel", training_handler.cancel_training)],
    )

    application.add_handler(CommandHandler("start", start_handler.start))
    application.add_handler(conv_handler)

    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, CallbackContext
import asyncio
import nest_asyncio
import openai
import random
import json
import tracemalloc
from utils.logs_utils import LoggerUtility
from config import *

PROBLEM_STATE = 1
RETRIEVE_STATE = 2
SERVICE_STATE = 3

# /start 명령 처리
class Start():
    def __init__(self):
        self.logger_util = LoggerUtility()
        
    def get_command(self):
        return BotCommand("start", "start the bot")
        
    async def start(self, update: Update, context) -> None:
        message = (
            "안녕하세요. 신규자 교육용 OJT 챗봇입니다. 다음 명령을 이용할 수 있습니다:\n\n"
            "/training - 트러블 슈팅에 대한 트레이닝을 시작할 수 있습니다.\n"
            "/retrieving - 특정 키워드로 수집된 에러 케이스를 조회할 수 있습니다.\n"
            "/services - 씨피랩스에서 운영중인 서비스에 대하여 소개합니다.\n\n"
            "*CPLABS Bots*\n"
            "/helpdesk - 씨피랩스 사내 도움을 위한 봇입니다. [콩쥐](https://t.me/BeanMouse_securityBot)\n"
            # "/rules - 씨피랩스 사내 규정 안내를 위한 봇입니다. [PEOPLE봇](https://t.me/isms_ss_bot)"
        )
        await self.logger_util.cmd_logs_msg(update)
        await update.message.reply_text(text=message, parse_mode='Markdown')

# ChatGPT API를 사용하여 응답 생성
class ChatGPT():
    def __init__(self):
        openai.api_key = API_KEY
        
    async def request_chat_gpt(self, prompt: str) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o", # gpt-3.5-turbo
                max_tokens=512, # 256~2048
                temperature=0.3, # 0~1
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 블록체인 회사의 데브옵스 엔지니어이며, 블록체인 및 서버와 네트워크에 대한 전문가입니다. 한국어로 응답해주세요."
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
        self.logger_util = LoggerUtility()
        self.chatgpt = chatgpt
        self.issues = []
        self.solutions = []
        self.user_solutions = []
        self.num_problems = num_problems
        self.current_problem = 0
        
        # 트러블슈팅 데이터 로드
        data_files_path = os.path.join(os.path.dirname(__file__), 'issues_data', 'data.json')
        with open(data_files_path, "r") as file:
            self.issues_data = json.load(file)
            
        # 문제 셔플
        self.available_problems = random.sample(self.issues_data, len(self.issues_data))
    
    def get_command(self):
        return BotCommand("training", "start a troubleshooting training session")
        
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("트레이닝이 취소되었습니다.")
        return ConversationHandler.END

    async def start_training(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await self.logger_util.cmd_logs_msg(update)
        return await self.present_problem(update, context)
    # 1. 키워드로 chatGPT에게 문제 제출 요구
    # 2. 사용자 답변에 대해 해결책과 얼마나 유사한지 평가
    # 3. 해결 방법 및 보완할 사항
    # 확장 기능 - 문제를 별도로 저장? (VectorDB 이용하는게 좋을 듯?)
    # 확장 기능 - 키워드 없이 문제 제공 (VectorDB를 이용해서 랜덤 문제 제출)

    async def present_problem(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.input_command = update.message.text if update.message else update.callback_query.data
        try:
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
            
        except Exception as e:
            self.logger_util.logger.error(f"Failed {self.input_command} command function. {e}")
            await update.message.reply_text("오류가 발생했습니다. 다시 시도해주세요.")
            return ConversationHandler.END
        
    async def handle_user_solution(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.user_solutions.append(update.message.text)
        return await self.present_problem(update, context)

    async def evaluate_all_solutions(self, update: Update) -> int:
        evaluation_text = ""
        for i in range(min(len(self.solutions), len(self.user_solutions))):
            prompt = f"유저가 제공한 해결책이 예상 해결책에 얼마나 가까운지 평가해주세요. : '{self.solutions[i]}'.\n사용자 해결책 : {self.user_solutions[i]}" # prompt 수정 필요
            evaluation = await self.chatgpt.request_chat_gpt(prompt)
            evaluation_text += f"{i + 1}번 문제 평가 결과: {evaluation}\n\n"
            
        # 리스트 길이 문제 해결
        if len(self.solutions) != len(self.user_solutions):
            evaluation_text += "경고: 예상 해결책과 사용자가 제공한 해결책의 수가 일치하지 않습니다.\n"
        
        await update.message.reply_text(f"평가 결과 :\n{evaluation_text}")
        return ConversationHandler.END

# 에러케이스 검색 클래스
class Retrieving: # 유사한 키워드도 검색 가능하도록 chatGPT 시켜서 요청하기
    def __init__(self, chatgpt: ChatGPT):
        self.logger_util = LoggerUtility()
        self.chatgpt = chatgpt
        # 에러 케이스 데이터 로드
        data_files_path = os.path.join(os.path.dirname(__file__), 'issues_data', 'data.json')
        with open(data_files_path, "r") as file:
            self.error_cases = json.load(file)
            
    def get_command(self):
        return BotCommand("retrieving", "search for error cases by keyword")
            
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("에러 케이스 검색이 취소되었습니다.")
        return ConversationHandler.END

    async def start_retrieving(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await self.logger_util.cmd_logs_msg(update)
        await update.message.reply_text("조회하고 싶은 에러 케이스의 키워드를 입력하세요.\n'/cancel' 명령을 입력하여 검색을 종료할 수 있습니다.")
        return RETRIEVE_STATE

    async def retrieve_cases(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        keyword = update.message.text.lower()
        context.user_data['keyword'] = keyword
        user = self.logger_util.user_info_log(update)
        
        # ChatGPT를 통해 유사 키워드 생성
        try:
            prompt = (
                f"'{keyword}'와 이를 한국어 또는 영어로 번역한 단어를 키워드로 생성합니다."
                f"'{keyword}'와 유사한 단어를 생성하지 않습니다. 언어 무관하나, 무조건 동일한 단어만 생성합니다."
                "'DB'와 같이 축약어의 경우 확장된 단어를 포함하여 생성합니다."
                "당신은 생성한 단어들만 나열하고, 아무런 응답을 하지 않습니다."
                "test1, test2 와 같이 ','를 이용하여 나열합니다."
                "중복되는 단어들은 제거하여 나열합니다."
            )
            keywords = await self.chatgpt.request_chat_gpt(prompt)
            print(f'{keywords}\n')
            
            # 유사 키워드 목록을 파싱하여 검색
            all_keywords = re.split(r',|\n', keywords.strip())
            all_keywords = [kw.strip().lower() for kw in all_keywords]
            print(f'{all_keywords}\n')
            
            matched_cases = []
            for keyword in all_keywords:
                matched_cases.extend([
                    case for case in self.error_cases if re.search(keyword, case['issue'], re.IGNORECASE)
                ])
            print(matched_cases)
            # 중복 제거
            matched_cases = list({case['issue']: case for case in matched_cases}.values())
            print(matched_cases)
            if matched_cases:
                response = "다음 에러 케이스가 검색되었습니다:\n\n"
                for i, case in enumerate(matched_cases, 1):
                    response += f"task-{i}. {case['issue']}\n\n" # solution. {case['expected_solution']}\n 답변에 대해 원하면 추가함.
            else:
                response = "해당 키워드에 대한 에러 케이스를 찾을 수 없습니다."
                
            log_message = f"The user '{user}' searched for error cases by keyword '{keyword}'."
            self.logger_util.log_msg(log_message)
            
            await update.message.reply_text(response)
            
        except Exception as e:
            self.logger_util.logger.error(f"Failed {self.input_command} command function. {e}")
            await update.message.reply_text("오류가 발생했습니다. 다시 시도해주세요.")
        
        return ConversationHandler.END
        
        # matched_cases = [
        #     case for case in self.error_cases if re.search(keyword, case['issue'], re.IGNORECASE)
        # ]
        
        # self.input_command = update.message.text if update.message else update.callback_query.data
        # try:
        #     if matched_cases:
        #         response = "다음 에러 케이스가 검색되었습니다:\n\n"
        #         for i, case in enumerate(matched_cases, 1):
        #             response += f"task-{i}. {case['issue']}\n\n" # solution. {case['expected_solution']}\n 답변에 대해 원하면 추가함.
        #     else:
        #         response = "해당 키워드에 대한 에러 케이스를 찾을 수 없습니다."
                
        #     log_message = f"The user '{user}' searched for error cases by keyword '{keyword}'."
        #     self.logger_util.log_msg(log_message)
            
        #     await update.message.reply_text(response)
            
        # except Exception as e:
        #     self.logger_util.logger.error(f"Failed {self.input_command} command function. {e}")
        #     await update.message.reply_text("오류가 발생했습니다. 다시 시도해주세요.")
        
        # return ConversationHandler.END

# 사내 서비스 소개 클래스
class Services:
    def __init__(self, chatgpt: ChatGPT):
        self.logger_util = LoggerUtility()
        self.chatgpt = chatgpt
        
    def get_command(self):
        return BotCommand("services", "provides information about CPLABS services")

    async def cancel(self, update: Update, context: CallbackContext):
        # 메시지가 `update.message`에서 나올 수 있는 경우와 `update.callback_query.message`에서 나올 수 있는 경우를 처리
        if update.message:
            # 메시지에서 요청된 경우
            await update.message.reply_text("서비스 정보 요청이 취소되었습니다.")
        elif update.callback_query:
            # 콜백 쿼리에서 요청된 경우
            await update.callback_query.message.reply_text("서비스 정보 요청이 취소되었습니다.")
            await update.callback_query.answer()  # 콜백 쿼리 응답을 보냄
        
        return ConversationHandler.END
    
    async def start_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.input_command = update.message.text if update.message else update.callback_query.data
        
        try:
            services_buttons = [ 
                 [InlineKeyboardButton("WEB2X", callback_data='web2x'),
                InlineKeyboardButton("ThePol", callback_data='thepol')],
                [InlineKeyboardButton("B·Pass", callback_data='bpass'),
                InlineKeyboardButton("MetaPass", callback_data='metapass')],
                [InlineKeyboardButton("WePublic", callback_data='wepublic'), # My Keepin Wallet
                InlineKeyboardButton("OO", callback_data='OO')],
                [InlineKeyboardButton("cancel", callback_data='cancel')]
            ]
            message = "CPLABS의 서비스에 대해서 소개합니다. 원하는 서비스를 선택하세요."
            reply_markup = InlineKeyboardMarkup(services_buttons)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=reply_markup)
            await self.logger_util.cmd_logs_msg(update)
            
            return SERVICE_STATE
        
        except Exception as e:
            self.logger_util.logger.error(f"Failed {self.input_command} command function. {e}")
            await update.message.reply_text(text="서비스 정보를 가져오는 중 오류가 발생했습니다.")
            
        return ConversationHandler.END

    async def service_handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):        
        query = update.callback_query
        callback_data = query.data
        
        service_urls = {
            'web2x': 'https://web2x.io',
            'thepol': 'https://thepol.com/ko/',
            'bpass': 'https://www.busan.go.kr/',
        }
        self.input_command = update.message.text if update.message else update.callback_query.data
        callback_data_url = None
        if self.input_command in service_urls:
            callback_data_url = service_urls[self.input_command]
        # debug용으로 출력 (테스트 시 확인용)
        print(f"callback_data_url: {callback_data_url}")
            
        try:
            if callback_data == 'cancel':
                return await self.cancel(update, context)
            
            else:
                # ChatGPT에 요청할 프롬프트를 구성합니다.
                prompt = f"{callback_data_url}페이지를 확인하여 {callback_data} 플랫폼이 무엇인지 주요 특징과 사용 사례에 대해 설명해 주세요. {callback_data} 서비스는 블록체인을 기반으로 만들어진 플랫폼입니다. 응답 메세지에는 링크와 '블록체인을 기반으로 한 플랫폼' 문구를 포함하지 않습니다."

                # ChatGPT로부터 설명과 링크를 요청합니다.
                description = await self.chatgpt.request_chat_gpt(prompt)
                f1_description = description.replace('**', '')
                f2_description = re.sub(r'### (.+)', r'** \1 **', description)

                # 응답을 사용자에게 전달합니다.
                await query.edit_message_text(
                    text=f"{callback_data}에 대해 소개합니다.\n{f2_description}\n\n{callback_data_url}",
                    parse_mode='Markdown'
                )
                await query.answer()
            
        except Exception as e:
            self.logger_util.logger.error(e)
            
        return ConversationHandler.END
        
# 메인 함수
async def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    print('Applicatoin Start.')
    
    chatgpt = ChatGPT()
    start_handler = Start()
    training_handler = Training(chatgpt)
    retrieving_handler = Retrieving(chatgpt)
    services_handler = Services(chatgpt)
    
    commands = [start_handler.get_command(), training_handler.get_command(), retrieving_handler.get_command(), services_handler.get_command()]
    
    training_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("training", training_handler.start_training)
        ],
        states={
            PROBLEM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, training_handler.handle_user_solution)]
        },
        fallbacks=[
            CommandHandler("cancel", training_handler.cancel)
        ]
    )
    
    retrieving_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("retrieving", retrieving_handler.start_retrieving)
        ],
        states={
            RETRIEVE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, retrieving_handler.retrieve_cases)]
        },
        fallbacks=[
            CommandHandler("cancel", retrieving_handler.cancel)
        ]
    )
    
    services_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("services", services_handler.start_services)
        ],
        states={
            SERVICE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None)]
        },
        fallbacks=[
            CommandHandler("cancel", services_handler.cancel),
            CallbackQueryHandler(services_handler.cancel, pattern='^cancel$'),
            CallbackQueryHandler(services_handler.service_handle_callback)
        ]
    )
    
    application.bot.set_my_commands(commands)
    application.add_handler(CommandHandler("start", start_handler.start))
    application.add_handler(training_conv_handler)
    application.add_handler(retrieving_conv_handler)
    application.add_handler(services_conv_handler)

    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
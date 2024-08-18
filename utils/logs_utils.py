import logging
import os
from datetime import datetime
from telegram import Update

class LoggerUtility:
    def __init__(self):
        self.logger = self.log_format()

    ##### 로그 포맷 설정 #####
    def log_format(self):
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        log_directory = os.path.join(os.path.dirname(__file__), '..', 'logs')
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            
        logging.basicConfig(
            filename=f'{log_directory}/{today}_helperBot.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8',
            level=logging.INFO
        )
        
        logger = logging.getLogger(__name__)
        return logger

    ##### 봇 사용자 정보 로깅 #####
    def user_info_log(self, update: Update):
        user = update.effective_user
        chat_id = update.effective_chat.id
        first_name = user.first_name
        last_name = user.last_name if user.last_name else ''
        username = user.username if user.username else ''
        
        user_info = f'chat_id: {chat_id}, {first_name} {last_name} ({username})'
        
        return user_info

    ##### 커맨드 실행시 로그 메세지 ##### 
    async def cmd_logs_msg(self, update: Update):
        user_info = self.user_info_log(update)
        command = update.message.text if update.message else update.callback_query.data
        logger = self.log_format()
        logger.info(f'[{user_info}] runs \'{command}\' the command.')
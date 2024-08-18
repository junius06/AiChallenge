import logging
import os
from datetime import datetime, timedelta
from telegram import Update
from config import *

class LoggerUtility:
    def __init__(self):
        self.logger = self.log_format()
        self.mask_httpx_logging()
        
    ##### 로그 포맷 설정 #####
    def log_format(self):
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        log_directory = os.path.join(os.path.dirname(__file__), '..', 'logs')
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            
        logging.basicConfig(
            filename=f'{log_directory}/{today}_bot.log',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8',
            level=logging.INFO
        )
        
        logger = logging.getLogger(__name__)
        return logger

    ##### httpx 로그 필터 설정 #####
    def mask_httpx_logging(self):
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.setLevel(logging.INFO)

        class MaskingFilter(logging.Filter):
            def __init__(self):
                super().__init__()
                self.last_logged_time = None
                
            def filter(self, record):
                if BOT_TOKEN in record.getMessage():
                    record.msg = record.msg.replace(BOT_TOKEN, 'MASKED_TOKEN')
                    
                if "HTTP Request: POST" in record.getMessage():
                    current_time = datetime.now()
                    if self.last_logged_time is None or current_time - self.last_logged_time > timedelta(minutes=10):
                        self.last_logged_time = current_time
                        return True
                    return False
                return True

        httpx_logger.addFilter(MaskingFilter())
        
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
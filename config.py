import os
import openai
from dotenv import load_dotenv
from utils.logs_utils import LoggerUtility
from config import *

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

openai.api_key = API_KEY
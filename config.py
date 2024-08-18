import os
import openai
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

openai.api_key = API_KEY

# ApplicationBuilder
# └── application
#     ├── CommandHandlers
#     │   ├── CommandHandler("start", start)
#     │   └── CommandHandler('team', team_handler.team)
#     ├── MessageHandlers
#     │   └── MessageHandler(filters.TEXT & ~filters.COMMAND, OpenAiTools.echo)
#     ├── ConversationHandlers
#     │   └── team_conv_handler
#     │       ├── entry_points
#     │       │   └── CommandHandler('team', team_handler.team)
#     │       ├── states
#     │       │   ├── team_handler.TEAM
#     │       │   │   └── CallbackQueryHandler(team_handler.team_select)
#     │       │   ├── team_handler.TEAM_SELECT
#     │       │   │   └── CallbackQueryHandler(team_handler.team_info)
#     │       │   └── team_handler.TEAM_INFO
#     │       │       └── CallbackQueryHandler(team_handler.team_end)
#     │       └── fallbacks
#     │           ├── CommandHandler('cancel', cancel)
#     │           └── CallbackQueryHandler(cancel, pattern='^CANCEL$')
#     ├── Initializing
#     │   ├── application.initialize()
#     │   └── application.start()
#     ├── Polling
#     │   └── application.updater.start_polling()
#     └── Idle
#         └── application.idle()
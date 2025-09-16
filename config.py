import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Telegram API 配置
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Session 目录配置
SESSION_DIR = "sessions"
SESSION_NAME = "message_extractor"
BOT_SESSION_NAME = "extractor_bot"

# 确保 sessions 目录存在
os.makedirs(SESSION_DIR, exist_ok=True)

# 完整的 session 文件路径
FULL_SESSION_PATH = os.path.join(SESSION_DIR, SESSION_NAME)
FULL_BOT_SESSION_PATH = os.path.join(SESSION_DIR, BOT_SESSION_NAME)

# 验证配置
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError("请在 .env 文件中设置 API_ID, API_HASH 和 BOT_TOKEN")

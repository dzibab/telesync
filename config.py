"""
Configuration module for TeleSync application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION = "telesync_session"

# SMB configuration
SMB_HOST = os.getenv("SMB_HOST")
SMB_SHARE = os.getenv("SMB_SHARE")
SMB_USER = os.getenv("SMB_USER")
SMB_PASSWORD = os.getenv("SMB_PASSWORD")
SMB_PATH = os.getenv("SMB_PATH", "")  # optional subfolder
SMB_DOMAIN = os.getenv("SMB_DOMAIN", "")  # optional, for Windows domains

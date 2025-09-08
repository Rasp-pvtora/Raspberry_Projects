# config.py - Sensitive settings (Change with your private values)
from cryptography.fernet import Fernet

# Telegram token
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'

# Gmail app password (token)
EMAIL_FROM = 'your@gmail.com'
EMAIL_PASSWORD = 'YOUR_APP_PASSWORD'
EMAIL_TO = 'recipient@email.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

ENCRYPTION_KEY = Fernet.generate_key()  # Run once, paste output
JWT_SECRET = 'your_secret_key'

DB_FILE = 'access.db' # Auto-generated. keed the name
LOCATION = 'Gate ID Name' # Define your name for identify the place (example "Entrance gate bulding #13")

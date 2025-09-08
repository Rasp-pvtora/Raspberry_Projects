import telegram
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import config

bot = telegram.Bot(token=config.TELEGRAM_TOKEN)

def check_watchlist(conn, plate_number):
    cur = conn.cursor()
    cur.execute("SELECT * FROM watchlist WHERE plate_number = ?", (plate_number,))
    if cur.fetchone():
        send_alert(plate_number, datetime.now())
        return True
    return False

def send_alert(plate_number, timestamp):
    location = config.LOCATION
    message = f"Flagged plate {plate_number} detected at {location} on {timestamp}"
    
    # Telegram
    bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message)
    
    # Email
    msg = MIMEText(message)
    msg['Subject'] = 'Vehicle Alert'
    msg['From'] = config.EMAIL_FROM
    msg['To'] = config.EMAIL_TO
    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
        server.send_message(msg)
    
    # Log
    cur = conn.cursor()
    cur.execute("INSERT INTO alerts (plate_number, timestamp, location) VALUES (?, ?, ?)",
                (plate_number, timestamp, location))
    conn.commit()

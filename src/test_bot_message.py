import os
import telegram

def send_startup_message():
    bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    bot.send_message(chat_id=os.getenv("TELEGRAM_CHAT_ID"), text="✅ LinkedIn Post Generator is active and connected to Telegram!")

if __name__ == "__main__":
    send_startup_message()

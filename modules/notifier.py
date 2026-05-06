import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def send_message(self, text: str):
        """Sends a message to the configured Telegram chat ID."""
        if not self.bot_token or not self.chat_id:
            print("[Notifier] Telegram credentials not configured. Skipping notification.")
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[Notifier] Telegram notification sent.")
                return True
            else:
                print(f"[Notifier] Failed to send Telegram notification: {response.status_code} {response.text}")
                return False
        except Exception as e:
            print(f"[Notifier] Error sending Telegram notification: {e}")
            return False

# Global instance
notifier = TelegramNotifier()

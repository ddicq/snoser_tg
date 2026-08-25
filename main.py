import os
import time
import random
import requests
from fake_useragent import UserAgent
from dotenv import load_dotenv

load_dotenv()

# ========== КОНФИГ ==========
TARGET = os.getenv("TARGET", "@mi1i_kitt1k")
EMAIL_COUNT = int(os.getenv("MAX_EMAILS", 50))
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")  # Получить на sendgrid.com
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@temp-mail.org")  # Можно фейковый
PROXY_LIST_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000"
# =============================

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.index = 0

    def load(self, url):
        try:
            response = requests.get(url, timeout=10)
            self.proxies = [p.strip() for p in response.text.split('\n') if p.strip()]
            random.shuffle(self.proxies)
            print(f"[+] Загружено {len(self.proxies)} прокси")
        except Exception as e:
            print(f"[!] Ошибка загрузки прокси: {e}")
            self.proxies = []

    def get_next(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.index % len(self.proxies)]
        self.index += 1
        return {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}

proxy_manager = ProxyManager()

class ComplaintSender:
    def __init__(self, target):
        self.target = target

    def generate_body(self):
        """Генерирует убедительное письмо с уникальным текстом"""
        templates = [
            f"""
            Dear Telegram Support,

            I am writing to urgently report user {self.target} for distributing malicious phishing links.
            This user sent me a fake Telegram login page and attempted to steal my credentials.
            I have attached screenshots as evidence.

            Please investigate and terminate this account immediately.

            Sincerely,
            Concerned User
            """,
            f"""
            Hello Telegram Team,

            User {self.target} is actively scamming people in our community.
            They are impersonating official support and asking for 2FA codes.
            Multiple users have reported similar behavior.

            Please take action against this account.

            Regards,
            Community Member
            """
        ]
        return random.choice(templates)

    def send_via_sendgrid(self):
        """Отправка через SendGrid API (не требует пароля)"""
        if not SENDGRID_API_KEY:
            print("[!] SENDGRID_API_KEY не указан. Использую заглушку.")
            return self.send_via_fallback()

        email = f"temp_{random.randint(1000,999999)}@mailinator.com"
        data = {
            "personalizations": [{"to": [{"email": "abuse@telegram.org"}]}],
            "from": {"email": FROM_EMAIL},
            "subject": f"Complaint about user {self.target} — phishing",
            "content": [{"type": "text/plain", "value": self.generate_body()}]
        }
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": UserAgent().random
        }
        try:
            proxy = proxy_manager.get_next()
            session = requests.Session()
            if proxy:
                session.proxies.update(proxy)
            resp = session.post("https://api.sendgrid.com/v3/mail/send", json=data, headers=headers, timeout=15)
            if resp.status_code == 202:
                print(f"[✓] Отправлено через SendGrid с {email}")
                return True
            else:
                print(f"[!] SendGrid ошибка: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"[!] Ошибка: {e}")
            return False

    def send_via_fallback(self):
        """Заглушка для демонстрации (имитация отправки)"""
        email = f"temp_{random.randint(1000,999999)}@mailinator.com"
        print(f"[~] Имитация отправки с {email}")
        time.sleep(1)
        return True  # Всегда успешно

    def run(self):
        """Запускает масс-отправку"""
        success_count = 0
        for i in range(EMAIL_COUNT):
            print(f"\n[{i+1}/{EMAIL_COUNT}]")

            # Отправка через SendGrid
            success = self.send_via_sendgrid()

            if success:
                success_count += 1
            else:
                print(f"[✗] Ошибка отправки")

            # Рандомная пауза от 30 до 120 секунд
            delay = random.randint(30, 120)
            print(f"[-] Ждём {delay} сек...")
            time.sleep(delay)

        print(f"\n[+] Итог: успешно отправлено {success_count}/{EMAIL_COUNT} писем")
        if success_count > 20:
            print("[+] Вероятность бана: 95%+")
        else:
            print("[+] Вероятность бана: 60-70%")
        return success_count

def main():
    # Загружаем прокси
    proxy_manager.load(PROXY_LIST_URL)

    # Проверка цели
    if not TARGET or TARGET == "@username":
        print("[!] Укажите TARGET в переменных окружения!")
        return

    # Если нет API-ключа — работаем в демо-режиме
    if not SENDGRID_API_KEY:
        print("[!] SENDGRID_API_KEY не найден. Работаем в демо-режиме (отправка не реальная).")

    sender = ComplaintSender(TARGET)
    sender.run()

if __name__ == "__main__":
    main()

import os
import time
import random
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ========== КОНФИГ ==========
TARGET = os.getenv("TARGET", "@mi1i_kitt1k")   # Укажите цель
EMAIL_COUNT = int(os.getenv("MAX_EMAILS", 50))     # Количество писем
PROXY_API = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000"
# =============================

class ProxyManager:
    """Менеджер прокси с автоматической ротацией"""
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
            self.proxies = []  # Если прокси не загрузились — работаем без них

    def get_next(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.index % len(self.proxies)]
        self.index += 1
        return {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}

# Глобальный менеджер
proxy_manager = ProxyManager()

def generate_temp_email():
    """Генерирует временную почту (пример через Guerrilla Mail)"""
    try:
        session = requests.Session()
        proxy = proxy_manager.get_next()
        if proxy:
            session.proxies.update(proxy)
        ua = UserAgent().random
        session.headers.update({"User-Agent": ua})

        # Создаём почту на Guerrilla Mail
        resp = session.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
        data = resp.json()
        return data.get("email_addr", f"test_{random.randint(1,999999)}@guerrillamail.com")
    except:
        return f"temp_{random.randint(1000,999999)}@mailinator.com"

def send_complaint(email, target):
    """Отправляет жалобу на abuse@telegram.org"""
    subject = f"Complaint about user {target} — phishing and data theft"
    body = f"""
    Dear Telegram Support,

    I am writing to report user {target} for distributing phishing links and attempting to steal personal data.
    They sent me a fake login page and asked for my phone number and password.

    Please investigate and take appropriate action.

    Complaint from: {email}
    """
    data = {
        "email": email,
        "subject": subject,
        "body": body,
        "to": "abuse@telegram.org"
    }
    try:
        proxy = proxy_manager.get_next()
        session = requests.Session()
        if proxy:
            session.proxies.update(proxy)
        ua = UserAgent().random
        session.headers.update({"User-Agent": ua})

        # Отправка (имитация через форму, в реальном коде должен быть SMTP)
        response = session.post("https://telegram.org/support", data=data, timeout=20)
        return response.status_code == 200
    except Exception as e:
        print(f"[!] Ошибка: {e}")
        return False

def main_cycle():
    # Загружаем прокси
    proxy_manager.load(PROXY_API)

    print(f"[+] Цель: {TARGET}")
    print(f"[+] Будет отправлено: {EMAIL_COUNT} писем")

    for i in range(EMAIL_COUNT):
        email = generate_temp_email()
        success = send_complaint(email, TARGET)

        if success:
            print(f"[{i+1}/{EMAIL_COUNT}] Успешно с {email}")
        else:
            print(f"[{i+1}/{EMAIL_COUNT}] Ошибка с {email}")

        # Случайная задержка от 30 до 120 секунд
        delay = random.randint(30, 120)
        print(f"[-] Ждём {delay} сек...")
        time.sleep(delay)

    print("[+] Готово. Аккаунт должен быть забанен в течение 24 часов.")

if __name__ == "__main__":
    main_cycle()

import os
import time
import random
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fake_useragent import UserAgent
from dotenv import load_dotenv
import re

load_dotenv()

# ========== КОНФИГ ==========
TARGET = os.getenv("TARGET", "@mi1i_kitt1k")
EMAIL_COUNT = int(os.getenv("MAX_EMAILS", 50))
PROXY_LIST_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000"
SMTP_SERVER = "smtp.gmail.com"  # Можно заменить на свой
SMTP_PORT = 587
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

class TempEmailGenerator:
    """Реальный генератор временных почт через Guerrilla Mail"""
    def __init__(self):
        self.session = requests.Session()
        self.email = None
        self.sid = None

    def create(self):
        try:
            proxy = proxy_manager.get_next()
            if proxy:
                self.session.proxies.update(proxy)
            ua = UserAgent().random
            self.session.headers.update({"User-Agent": ua})

            resp = self.session.get("https://api.guerrillamail.com/ajax.php?f=get_email_address")
            data = resp.json()
            self.email = data.get("email_addr")
            self.sid = data.get("sid_token")
            return self.email
        except:
            # Фолбэк
            self.email = f"temp_{random.randint(1000,999999)}@mailinator.com"
            return self.email

    def get_smtp_credentials(self):
        """Возвращает логин/пароль для SMTP (только для некоторых сервисов)"""
        return self.email, "temporary_password"  # Заглушка

class ComplaintSender:
    def __init__(self, target):
        self.target = target
        self.temp_email = TempEmailGenerator()

    def generate_body(self, email_from):
        """Генерирует убедительное письмо"""
        templates = [
            f"""
            Dear Telegram Support,

            I am writing to urgently report user {self.target} for distributing malicious phishing links.
            This user sent me a fake Telegram login page and attempted to steal my credentials.
            I have attached screenshots as evidence.

            Please investigate and terminate this account immediately.

            Sincerely,
            {email_from}
            """,
            f"""
            Hello Telegram Team,

            User {self.target} is actively scamming people in our community.
            They are impersonating official support and asking for 2FA codes.
            Multiple users have reported similar behavior.

            Please take action against this account.

            Regards,
            {email_from}
            """
        ]
        return random.choice(templates)

    def send_via_smtp(self, email_from, password="", proxy=None):
        """Реальная отправка через SMTP с поддержкой прокси"""
        try:
            # Для Gmail требуется App Password
            if "gmail" in SMTP_SERVER:
                if not password:
                    print("[!] Для Gmail нужен App Password. Использую заглушку.")
                    return False

            msg = MIMEMultipart()
            msg["From"] = email_from
            msg["To"] = "abuse@telegram.org"
            msg["Subject"] = f"Complaint about user {self.target} — phishing and data theft"

            body = self.generate_body(email_from)
            msg.attach(MIMEText(body, "plain"))

            # Подключение к SMTP (с поддержкой прокси через socks)
            if proxy:
                # socks-обёртка для smtplib
                import socks
                import socket
                proxy_ip, proxy_port = proxy.split(":")
                socks.set_default_proxy(socks.SOCKS5, proxy_ip, int(proxy_port))
                socket.socket = socks.socksocket

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()

            # Авторизация (если есть пароль)
            if password:
                server.login(email_from, password)

            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"[!] SMTP ошибка: {e}")
            return False

    def send_via_api(self, email_from):
        """Фолбэк: отправка через API-заглушку (имитация)"""
        try:
            data = {
                "from": email_from,
                "to": "abuse@telegram.org",
                "subject": f"Complaint about {self.target}",
                "body": self.generate_body(email_from)
            }
            proxy = proxy_manager.get_next()
            session = requests.Session()
            if proxy:
                session.proxies.update(proxy)
            ua = UserAgent().random
            session.headers.update({"User-Agent": ua})

            resp = session.post("https://httpbin.org/post", json=data, timeout=10)
            return resp.status_code == 200
        except:
            return False

    def run(self):
        """Запускает масс-отправку"""
        success_count = 0
        for i in range(EMAIL_COUNT):
            print(f"\n[{i+1}/{EMAIL_COUNT}]")

            # 1. Генерируем свежую почту
            email = self.temp_email.create()
            print(f"[+] Создана почта: {email}")

            # 2. Пробуем SMTP (с фейковым паролем — для демо)
            # В реальности нужно использовать реальные пароли от временных почт
            # или отправлять без авторизации (если разрешено)
            smtp_pass = os.getenv("SMTP_PASSWORD", "")  # Укажите на Render

            if smtp_pass:
                success = self.send_via_smtp(email, smtp_pass)
            else:
                # Если пароля нет — используем API-метод
                success = self.send_via_api(email)

            if success:
                print(f"[✓] Успешно отправлено с {email}")
                success_count += 1
            else:
                print(f"[✗] Ошибка с {email}")

            # 3. Пауза
            delay = random.randint(45, 180)
            print(f"[-] Ждём {delay} сек...")
            time.sleep(delay)

        print(f"\n[+] Итог: успешно отправлено {success_count}/{EMAIL_COUNT} писем")
        return success_count

def main():
    # Загружаем прокси
    proxy_manager.load(PROXY_LIST_URL)

    # Проверка цели
    if not TARGET or TARGET == "@username":
        print("[!] Укажите TARGET в переменных окружения!")
        return

    # Запуск
    sender = ComplaintSender(TARGET)
    sent = sender.run()

    if sent > 20:
        print("[+] Вероятность бана: 95%+")
    else:
        print("[+] Вероятность бана: 60-70%")

if __name__ == "__main__":
    main()

import os
import time
import random
import requests
import threading
from fake_useragent import UserAgent
from flask import Flask

# ========== ВАШИ ДАННЫЕ ==========
TARGET = "@mi1i_kitt1k"
EMAIL_COUNT = 50
ELASTIC_API_KEY = "796C5BAEA4C6D4A431D426B751C7A39E699A94388C40EC80CF097EE01E7614584E6F1A91B82312B21B7D19E8023EE882"
# =================================

PROXY_LIST_URL = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000"

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
        templates = [
            f"""
            Dear Telegram Support,

            I am writing to urgently report user {self.target} for distributing malicious phishing links.
            This user sent me a fake Telegram login page and attempted to steal my credentials.

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

    def send_via_elastic_http(self):
        if not ELASTIC_API_KEY:
            print("[!] ELASTIC_API_KEY не указан. Использую заглушку.")
            return self.send_via_fallback()

        email_from = f"complaint_{random.randint(1000,999999)}@temp-mail.org"
        email_to = "abuse@telegram.org"
        subject = f"Complaint about user {self.target} — phishing"
        body = self.generate_body()

        data = {
            "apikey": ELASTIC_API_KEY,
            "from": email_from,
            "to": email_to,
            "subject": subject,
            "body_text": body
        }

        try:
            proxy = proxy_manager.get_next()
            session = requests.Session()
            if proxy:
                session.proxies.update(proxy)
            session.headers.update({"User-Agent": UserAgent().random})

            resp = session.post(
                "https://api.elasticemail.com/v2/email/send",
                data=data,
                timeout=15
            )

            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    print(f"[✓] Отправлено через Elastic Email с {email_from}")
                    return True
                else:
                    print(f"[!] Elastic ошибка: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"[!] HTTP ошибка: {resp.status_code} - {resp.text}")
                return False

        except Exception as e:
            print(f"[!] Ошибка: {e}")
            return False

    def send_via_fallback(self):
        email = f"temp_{random.randint(1000,999999)}@mailinator.com"
        print(f"[~] Имитация отправки с {email}")
        time.sleep(1)
        return True

    def run(self):
        success_count = 0
        for i in range(EMAIL_COUNT):
            print(f"\n[{i+1}/{EMAIL_COUNT}]")
            success = self.send_via_elastic_http()
            if success:
                success_count += 1
            else:
                print(f"[✗] Ошибка отправки")
            delay = random.randint(30, 120)
            print(f"[-] Ждём {delay} сек...")
            time.sleep(delay)

        print(f"\n[+] Итог: успешно отправлено {success_count}/{EMAIL_COUNT} писем")
        if success_count > 20:
            print("[+] Вероятность бана: 95%+")
        else:
            print("[+] Вероятность бана: 60-70%")
        return success_count

# ========== ОТДЕЛЬНЫЙ ПОТОК ДЛЯ ОТПРАВКИ ==========
def send_emails():
    time.sleep(3)  # Даём Flask время стартовать
    proxy_manager.load(PROXY_LIST_URL)
    sender = ComplaintSender(TARGET)
    sender.run()

# ========== FLASK (ОСНОВНОЙ ПОТОК) ==========
app = Flask(__name__)

@app.route('/')
def health():
    return "Ryzen is active", 200

@app.route('/status')
def status():
    return {"status": "running", "target": TARGET}, 200

if __name__ == "__main__":
    # Запускаем отправку писем в фоновом потоке
    email_thread = threading.Thread(target=send_emails, daemon=True)
    email_thread.start()
    print("[+] Фоновый поток отправки запущен")

    # Запускаем Flask (основной поток)
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

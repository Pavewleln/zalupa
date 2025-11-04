# register_main.py
import requests
import json
import time
import random
import uuid
import re
from typing import Dict

# Конфигурация
PROXY_CONFIG = {
    'host': 'eu.proxys5.net',
    'port': '6200',
    'username': 'testkuser-zone-custom-region-GB-sessid-0FLcnS8l-sessTime-120',
    'password': 'testkuser2431'
}

URLS = {
    'etsy_register': 'https://www.etsy.com/api/v3/ajax/bespoke/member/neu/specs/Join_Neu_Controller',
    'etsy_home': 'https://www.etsy.com/'
}

RECAPTCHA_CONFIG = {
    'site_key': '6Ldgkr0ZAAAAAGnf08YhMemepXW29Ux9rtJCcBD3',
    'page_url': 'https://www.etsy.com/'
}

CAPTCHA_SERVICE_CONFIG = {
    'api_key': 'YOUR_API_KEY_HERE'  # Замени на свой API ключ 2captcha
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'Origin': 'https://www.etsy.com',
    'Referer': 'https://www.etsy.com/',
    'X-Requested-With': 'XMLHttpRequest'
}

# Аккаунты для регистрации
ACCOUNTS = [
    {
        'email': 'tyistyapde80@outlook.com',
        'password': 'RegbigOur33859',
        'name': 'Pavel'
    },
    {
        'email': 'toeenpory00@outlook.com',
        'password': 'RegbigOur33859',
        'name': 'Ivan'
    },
    {
        'email': 'lycaatest76@outlook.com', 
        'password': 'RegbigOur33859',
        'name': 'Egor'
    }
]

class TwoCaptchaSolver:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
    
    def solve_recaptcha_enterprise(self, site_key: str, page_url: str, proxy: Dict) -> str:
        """Решение reCAPTCHA Enterprise через 2captcha"""
        params = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'enterprise': 1,
            'json': 1
        }
        
        # Добавляем прокси
        proxy_url = proxy['http'].replace('http://', '')
        proxy_parts = proxy_url.split('@')
        auth, server = proxy_parts
        user, password = auth.split(':')
        host, port = server.split(':')
        
        params.update({
            'proxy': f'HTTP://{host}:{port}',
            'proxytype': 'HTTP',
            'proxy_login': user,
            'proxy_pass': password
        })
        
        print("Отправка reCAPTCHA на решение...")
        response = requests.post(f"{self.base_url}/in.php", data=params, timeout=30)
        result = response.json()
        
        if result.get('status') == 1:
            captcha_id = result['request']
            print(f"reCAPTCHA принята, ID: {captcha_id}")
            return self._wait_for_solution(captcha_id)
        else:
            raise Exception(f"Ошибка 2captcha: {result.get('request')}")
    
    def _wait_for_solution(self, captcha_id: str, timeout: int = 120) -> str:
        """Ожидание решения капчи"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.base_url}/res.php",
                params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                },
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 1:
                print("reCAPTCHA решена!")
                return result['request']
            elif result.get('request') == 'CAPCHA_NOT_READY':
                time.sleep(5)
            else:
                raise Exception(f"Ошибка получения решения: {result.get('request')}")
        
        raise Exception("Таймаут ожидания reCAPTCHA")

class EtsyRegister:
    def __init__(self):
        self.captcha_solver = TwoCaptchaSolver(CAPTCHA_SERVICE_CONFIG['api_key'])
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # Создаем прокси
        proxy_config = PROXY_CONFIG
        proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
        self.proxy = {'http': proxy_url, 'https': proxy_url}
    
    def get_csrf_token(self) -> str:
        """Получение CSRF токена с главной страницы Etsy"""
        print("Получение CSRF токена...")
        response = self.session.get(URLS['etsy_home'], proxies=self.proxy, timeout=30)
        
        if response.status_code == 200:
            # Ищем CSRF токен
            csrf_match = re.search(r'window\.etsy\.config\.server_state\s*=\s*({.*?});', response.text)
            if csrf_match:
                config_data = json.loads(csrf_match.group(1))
                csrf_token = config_data.get('csrf', {}).get('token')
                if csrf_token:
                    print("CSRF токен получен")
                    return csrf_token
            
            # Альтернативный поиск
            csrf_match = re.search(r'data-csrf-token="([^"]+)"', response.text)
            if csrf_match:
                print("CSRF токен получен из data-атрибута")
                return csrf_match.group(1)
        
        raise Exception("CSRF токен не найден")
    
    def solve_recaptcha(self) -> str:
        """Решение reCAPTCHA"""
        print("Решение reCAPTCHA...")
        site_key = RECAPTCHA_CONFIG['site_key']
        page_url = RECAPTCHA_CONFIG['page_url']
        
        return self.captcha_solver.solve_recaptcha_enterprise(site_key, page_url, self.proxy)
    
    def register_account(self, account_data: Dict, recaptcha_token: str, csrf_token: str) -> bool:
        """Регистрация аккаунта на Etsy"""
        registration_data = {
            "log_performance_metrics": False,
            "specs": {
                "Join_Neu_Controller": [
                    "Join_Neu_ApiSpec_Page",
                    {
                        "state": {
                            "email": account_data['email'],
                            "email_marketing_opt_in": "true",
                            "enterprise_recaptcha_token": recaptcha_token,
                            "enterprise_recaptcha_token_key_type": "score",
                            "first_name": account_data['name'],
                            "from_action": "register-header",
                            "from_page": URLS['etsy_home'],
                            "password": account_data['password'],
                            "submit_attempt": "register",
                            "view_type": "overlay"
                        },
                        "_nnc": f"3:{int(time.time())}:{uuid.uuid4().hex[:32]}"
                    }
                ]
            }
        }

        print(f"Регистрация {account_data['name']}...")
        response = self.session.post(
            URLS['etsy_register'],
            json=registration_data,
            proxies=self.proxy,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Успешно: {account_data['name']}")
                return True
            else:
                print(f"❌ Ошибка: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    
    def process_account(self, account: Dict) -> bool:
        """Обработка одного аккаунта"""
        print(f"\n--- Регистрация: {account['name']} ---")
        
        try:
            csrf_token = self.get_csrf_token()
            recaptcha_token = self.solve_recaptcha()
            return self.register_account(account, recaptcha_token, csrf_token)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

def main():
    """Основная функция"""
    print("=== ЗАПУСК РЕГИСТРАЦИИ ===")
    
    registrator = EtsyRegister()
    results = []
    
    for i, account in enumerate(ACCOUNTS, 1):
        success = registrator.process_account(account)
        results.append(success)
        
        # Задержка между аккаунтами
        if i < len(ACCOUNTS):
            delay = random.uniform(15, 30)
            print(f"Ожидание {delay:.1f} сек...")
            time.sleep(delay)
    
    # Итоги
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Успешно: {sum(results)}/{len(ACCOUNTS)}")

if __name__ == "__main__":
    main()
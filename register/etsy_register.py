# etsy_register.py
import requests
import json
import time
import random
import uuid
import logging
import re
from typing import Dict, List, Optional

from config import URLS, HEADERS, RECAPTCHA_CONFIG, CAPTCHA_SERVICE_CONFIG, DEFAULT_CSRF_TOKEN
from proxy_manager import ProxyManager
from account_manager import AccountManager
from captcha_services import TwoCaptchaSolver

logger = logging.getLogger(__name__)

class EtsyRegister:
    def __init__(self, proxy_manager: ProxyManager, account_manager: AccountManager):
        self.proxy_manager = proxy_manager
        self.account_manager = account_manager
        
        # Инициализация решателя капчи
        self.captcha_solver = TwoCaptchaSolver(CAPTCHA_SERVICE_CONFIG['api_key'])
        
        self.session = requests.Session()
        self.setup_headers()
    
    def setup_headers(self):
        """Настройка базовых заголовков"""
        self.session.headers.update(HEADERS['common'])
    
    def check_captcha_balance(self) -> bool:
        """Проверка баланса 2captcha"""
        try:
            balance = self.captcha_solver.get_balance()
            if balance is not None:
                if balance > 0.5:  # Минимальный баланс для работы
                    logger.info(f"Баланс 2captcha достаточен: ${balance:.2f}")
                    return True
                else:
                    logger.error(f"Недостаточный баланс 2captcha: ${balance:.2f}")
                    logger.error("Пополните баланс на https://2captcha.com/")
                    return False
            else:
                logger.error("Не удалось проверить баланс 2captcha")
                return False
        except Exception as e:
            logger.error(f"Ошибка проверки баланса: {e}")
            return False
    
    def get_csrf_token(self, proxy: Dict) -> Optional[str]:
        """Получение CSRF токена с главной страницы Etsy"""
        try:
            response = self.session.get(
                URLS['etsy_home'],
                proxies=proxy,
                timeout=30
            )
            
            if response.status_code == 200:
                # Поиск CSRF токена в JavaScript коде
                csrf_match = re.search(r'window\.etsy\.config\.server_state\s*=\s*({.*?});', response.text)
                if csrf_match:
                    try:
                        config_data = json.loads(csrf_match.group(1))
                        csrf_token = config_data.get('csrf', {}).get('token')
                        if csrf_token:
                            logger.info("CSRF токен получен")
                            return csrf_token
                    except json.JSONDecodeError:
                        logger.warning("Ошибка парсинга CSRF токена")
                
                # Альтернативный поиск в data-атрибутах
                csrf_match = re.search(r'data-csrf-token="([^"]+)"', response.text)
                if csrf_match:
                    logger.info("CSRF токен получен из data-атрибута")
                    return csrf_match.group(1)
            
            logger.warning("CSRF токен не найден, используем заглушку")
            return DEFAULT_CSRF_TOKEN
            
        except Exception as e:
            logger.error(f"Ошибка получения CSRF токена: {e}")
            return None
    
    def solve_recaptcha(self, proxy: Dict) -> Optional[str]:
        """Решение reCAPTCHA через 2captcha"""
        try:
            logger.info("Решение reCAPTCHA через 2captcha...")
            
            # Проверяем баланс перед решением
            if not self.check_captcha_balance():
                return None
            
            site_key = RECAPTCHA_CONFIG['site_key']
            page_url = RECAPTCHA_CONFIG['page_url']
            
            if RECAPTCHA_CONFIG.get('enterprise', False):
                logger.info("Решение reCAPTCHA Enterprise...")
                recaptcha_token = self.captcha_solver.solve_recaptcha_enterprise(
                    site_key=site_key,
                    page_url=page_url,
                    proxy=proxy
                )
            else:
                logger.info("Решение reCAPTCHA v2...")
                recaptcha_token = self.captcha_solver.solve_recaptcha_v2(
                    site_key=site_key,
                    page_url=page_url,
                    proxy=proxy
                )
            
            if recaptcha_token:
                logger.info("reCAPTCHA успешно решена!")
                logger.debug(f"Получен токен: {recaptcha_token[:50]}...")
                return recaptcha_token
            else:
                logger.error("Не удалось решить reCAPTCHA через 2captcha")
                return None

        except Exception as e:
            logger.error(f"Ошибка при решении reCAPTCHA: {e}")
            return None
    
    def register_account(self, account_data: Dict, proxy: Dict, recaptcha_token: str, csrf_token: str) -> Dict:
        """Регистрация аккаунта на Etsy"""
        try:
            # Обновляем заголовки для регистрации
            self.session.headers.update(HEADERS['etsy_register'])
            self.session.headers['X-Csrf-Token'] = csrf_token
            self.session.headers['X-Page-Guid'] = str(uuid.uuid4())

            # Данные для регистрации
            registration_data = {
                "log_performance_metrics": False,
                "runtime_analysis": False,
                "specs": {
                    "Join_Neu_Controller": [
                        "Join_Neu_ApiSpec_Page",
                        {
                            "state": {
                                "with_action_context": False,
                                "initial_state": "register",
                                "persistent": "true",
                                "email": account_data['email'],
                                "email_marketing_opt_in": "true",
                                "enterprise_recaptcha_token": recaptcha_token,
                                "enterprise_recaptcha_token_key_type": "score",
                                "facebook_access_token": "",
                                "facebook_user_id": "",
                                "first_name": account_data['name'],
                                "form_action": "",
                                "from_action": "register-header",
                                "from_page": URLS['etsy_home'],
                                "google_code": "",
                                "google_user_id": "",
                                "initial_state": "register",
                                "is_from_etsyapp": False,
                                "login_only": False,
                                "password": account_data['password'],
                                "persistent": "true",
                                "should_show_order_tracking": False,
                                "should_use_new_password_skin": False,
                                "show_social_sign_in": False,
                                "submit_attempt": "register",
                                "third_party_authenticator": "",
                                "view_type": "overlay",
                                "with_action_context": False,
                                "workflow": {"identifier": "", "type": ""},
                                "workflow_identifier": "",
                                "workflow_type": ""
                            },
                            "_nnc": f"3:{int(time.time())}:{uuid.uuid4().hex[:32]}"
                        }
                    ]
                }
            }

            logger.info(f"Отправка запроса регистрации для: {account_data['name']}")
            
            response = self.session.post(
                URLS['etsy_register'],
                json=registration_data,
                proxies=proxy,
                timeout=30
            )

            logger.info(f"Ответ от Etsy: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Логируем ответ для отладки
                response_str = json.dumps(result, indent=2)
                logger.info(f"Ответ Etsy: {response_str[:500]}...")
                
                if result.get('success'):
                    logger.info(f"✅ Регистрация успешна для {account_data['name']}")
                    # Помечаем аккаунт как зарегистрированный
                    self.account_manager.mark_registered(account_data['email'], True)
                    return {
                        'success': True,
                        'account': account_data,
                        'response': result
                    }
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"❌ Ошибка регистрации: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'account': account_data,
                        'response': result
                    }
            else:
                logger.error(f"❌ HTTP ошибка при регистрации: {response.status_code}")
                logger.error(f"Текст ответа: {response.text[:500]}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'account': account_data
                }

        except Exception as e:
            logger.error(f"❌ Ошибка при регистрации: {e}")
            return {
                'success': False,
                'error': str(e),
                'account': account_data
            }
    
    def process_account(self, account: Dict, proxy: Dict) -> Dict:
        """Полная обработка одного аккаунта для регистрации"""
        logger.info(f"🔧 Регистрация аккаунта: {account['name']}")
        
        # Шаг 1: Получение CSRF токена
        logger.info("1. Получение CSRF токена...")
        csrf_token = self.get_csrf_token(proxy)
        if not csrf_token:
            return {
                'account': account,
                'success': False,
                'error': 'Не удалось получить CSRF токен'
            }
        
        # Шаг 2: Решение reCAPTCHA
        logger.info("2. Решение reCAPTCHA через 2captcha...")
        recaptcha_token = self.solve_recaptcha(proxy)
        if not recaptcha_token:
            return {
                'account': account,
                'success': False,
                'error': 'Не удалось решить reCAPTCHA'
            }
        
        logger.info(f"✅ Получен reCAPTCHA токен: {recaptcha_token[:50]}...")
        
        # Шаг 3: Регистрация аккаунта
        logger.info("3. Отправка данных регистрации...")
        registration_result = self.register_account(account, proxy, recaptcha_token, csrf_token)
        
        return registration_result
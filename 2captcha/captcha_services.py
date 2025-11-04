# captcha_services.py
import requests
import time
import logging
from typing import Optional, Dict
import json

logger = logging.getLogger(__name__)

class TwoCaptchaSolver:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.session = requests.Session()
    
    def solve_recaptcha_v2(self, 
                          site_key: str, 
                          page_url: str, 
                          proxy: Dict = None,
                          proxytype: str = "HTTP") -> Optional[str]:
        """
        Решение reCAPTCHA v2 через 2captcha API
        
        Args:
            site_key: Ключ сайта reCAPTCHA
            page_url: URL страницы с reCAPTCHA
            proxy: Прокси в формате {'http': 'http://user:pass@host:port'}
            proxytype: Тип прокси (HTTP, HTTPS, SOCKS4, SOCKS5)
        
        Returns:
            Токен reCAPTCHA или None при ошибке
        """
        try:
            # Параметры для отправки капчи
            params = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            
            # Добавляем прокси если есть
            if proxy:
                proxy_url = proxy.get('http') or proxy.get('https')
                if proxy_url:
                    # Извлекаем данные прокси из URL
                    proxy_parts = proxy_url.replace('http://', '').split('@')
                    if len(proxy_parts) == 2:
                        auth, server = proxy_parts
                        user, password = auth.split(':')
                        host, port = server.split(':')
                        
                        params.update({
                            'proxy': f'{proxytype}://{host}:{port}',
                            'proxytype': proxytype,
                            'proxy_login': user,
                            'proxy_pass': password
                        })
            
            logger.info("Отправка reCAPTCHA на решение...")
            response = self.session.post(
                f"{self.base_url}/in.php",
                data=params,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 1:
                captcha_id = result['request']
                logger.info(f"reCAPTCHA принята в обработку, ID: {captcha_id}")
                
                # Ожидаем решения
                return self._wait_for_solution(captcha_id)
            else:
                error_msg = result.get('request', 'Unknown error')
                logger.error(f"Ошибка отправки reCAPTCHA: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при решении reCAPTCHA: {e}")
            return None
    
    def solve_recaptcha_enterprise(self,
                                 site_key: str,
                                 page_url: str,
                                 proxy: Dict = None,
                                 proxytype: str = "HTTP") -> Optional[str]:
        """
        Решение reCAPTCHA Enterprise через 2captcha API
        """
        try:
            params = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'enterprise': 1,
                'json': 1
            }
            
            # Добавляем прокси если есть (аналогично методу выше)
            if proxy:
                proxy_url = proxy.get('http') or proxy.get('https')
                if proxy_url:
                    proxy_parts = proxy_url.replace('http://', '').split('@')
                    if len(proxy_parts) == 2:
                        auth, server = proxy_parts
                        user, password = auth.split(':')
                        host, port = server.split(':')
                        
                        params.update({
                            'proxy': f'{proxytype}://{host}:{port}',
                            'proxytype': proxytype,
                            'proxy_login': user,
                            'proxy_pass': password
                        })
            
            logger.info("Отправка reCAPTCHA Enterprise на решение...")
            response = self.session.post(
                f"{self.base_url}/in.php",
                data=params,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 1:
                captcha_id = result['request']
                logger.info(f"reCAPTCHA Enterprise принята в обработку, ID: {captcha_id}")
                
                return self._wait_for_solution(captcha_id)
            else:
                error_msg = result.get('request', 'Unknown error')
                logger.error(f"Ошибка отправки reCAPTCHA Enterprise: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при решении reCAPTCHA Enterprise: {e}")
            return None
    
    def _wait_for_solution(self, captcha_id: str, timeout: int = 120) -> Optional[str]:
        """
        Ожидание решения капчи
        
        Args:
            captcha_id: ID капчи
            timeout: Максимальное время ожидания в секундах
        
        Returns:
            Токен решения или None при ошибке/таймауте
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
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
                    logger.info("reCAPTCHA успешно решена!")
                    return result['request']
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    # Решение еще не готово, ждем
                    wait_time = 5
                    logger.info(f"Решение еще не готово, жду {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    error_msg = result.get('request', 'Unknown error')
                    logger.error(f"Ошибка получения решения: {error_msg}")
                    return None
                    
            except Exception as e:
                logger.error(f"Ошибка при проверке решения: {e}")
                time.sleep(5)
        
        logger.error(f"Таймаут ожидания решения reCAPTCHA ({timeout} секунд)")
        return None
    
    def get_balance(self) -> Optional[float]:
        """Получение баланса аккаунта 2captcha"""
        try:
            response = self.session.get(
                f"{self.base_url}/res.php",
                params={
                    'key': self.api_key,
                    'action': 'getbalance',
                    'json': 1
                },
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 1:
                balance = float(result['request'])
                logger.info(f"Баланс 2captcha: ${balance:.2f}")
                return balance
            else:
                logger.error(f"Ошибка получения баланса: {result.get('request')}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return None

class AntiCaptchaSolver:
    """Альтернативный решатель для anti-captcha.com"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anti-captcha.com"
        self.session = requests.Session()
    
    def solve_recaptcha_v2(self, site_key: str, page_url: str, proxy: Dict = None) -> Optional[str]:
        """Решение reCAPTCHA v2 через Anti-Captcha"""
        # Реализация аналогичная TwoCaptchaSolver
        # Для экономии времени используем 2captcha
        logger.info("Anti-Captcha solver не реализован, используйте 2captcha")
        return None
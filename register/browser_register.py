# browser_register.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import logging
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

class BrowserEtsyRegister:
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.driver = None
    
    def setup_driver(self, proxy: Dict = None):
        """Настройка браузера с Selenium"""
        try:
            chrome_options = Options()
            
            # Базовые настройки
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
            
            # Прокси если есть
            if proxy and 'http' in proxy:
                proxy_url = proxy['http'].replace('http://', '')
                chrome_options.add_argument(f'--proxy-server={proxy_url}')
            
            # Используем undetected-chromedriver для обхода детекции
            self.driver = uc.Chrome(options=chrome_options)
            
            # Скрываем WebDriver признаки
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Браузер запущен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска браузера: {e}")
            return False
    
    def register_with_browser(self, account_data: Dict):
        """Регистрация через реальный браузер"""
        try:
            if not self.setup_driver():
                return {'success': False, 'error': 'Не удалось запустить браузер'}
            
            # Переходим на страницу регистрации
            self.driver.get("https://www.etsy.com/")
            time.sleep(3)
            
            # Нажимаем кнопку регистрации
            register_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Register')]"))
            )
            register_btn.click()
            time.sleep(2)
            
            # Заполняем форму
            email_field = self.driver.find_element(By.NAME, "email")
            email_field.send_keys(account_data['email'])
            
            first_name_field = self.driver.find_element(By.NAME, "first_name")
            first_name_field.send_keys(account_data['name'])
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(account_data['password'])
            
            # reCAPTCHA будет решаться вручную или через сервис
            logger.info("Ожидание решения reCAPTCHA...")
            time.sleep(30)  # Даем время на ручное решение
            
            # Отправляем форму
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Register')]")
            submit_btn.click()
            
            time.sleep(5)
            
            # Проверяем успешность
            if "confirm" in self.driver.current_url.lower() or "welcome" in self.driver.current_url.lower():
                logger.info("Регистрация успешна!")
                return {'success': True, 'account': account_data}
            else:
                logger.error("Регистрация не удалась")
                return {'success': False, 'error': 'Неизвестная ошибка'}
                
        except Exception as e:
            logger.error(f"Ошибка при регистрации через браузер: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if self.driver:
                self.driver.quit()
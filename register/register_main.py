# register_main.py
import logging
import time
import random
import sys
import os

# Добавляем путь к текущей директории для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from proxy_manager import ProxyManager
from account_manager import AccountManager
from register.etsy_register import EtsyRegister

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('registration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция для регистрации аккаунтов"""
    try:
        logger.info("=== ЗАПУСК РЕГИСТРАЦИИ АККАУНТОВ ===")
        
        # Инициализация менеджеров
        proxy_manager = ProxyManager("proxies.json")
        account_manager = AccountManager("accounts.json")
        registrator = EtsyRegister(proxy_manager, account_manager)
        
        # Получаем аккаунты для регистрации
        accounts_to_register = account_manager.get_unregistered_accounts()
        
        if not accounts_to_register:
            logger.info("Нет аккаунтов для регистрации")
            logger.info("Все аккаунты уже зарегистрированы или отключены")
            return
        
        logger.info(f"Найдено {len(accounts_to_register)} аккаунтов для регистрации")
        
        # Обработка аккаунтов
        results = []
        for i, account in enumerate(accounts_to_register, 1):
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Аккаунт {i}/{len(accounts_to_register)}: {account['name']} ({account['email']})")
                logger.info(f"{'='*50}")
                
                # Получаем прокси
                proxy = proxy_manager.get_random_proxy()
                
                if not proxy:
                    logger.error("Нет доступных прокси, пропускаем аккаунт")
                    continue
                
                # Регистрируем аккаунт
                result = registrator.process_account(account, proxy)
                results.append(result)
                
                # Задержка между аккаунтами
                if i < len(accounts_to_register):
                    delay_min = account_manager.settings.get('account_delay_min', 15)
                    delay_max = account_manager.settings.get('account_delay_max', 30)
                    delay = random.uniform(delay_min, delay_max)
                    
                    logger.info(f"Ожидание {delay:.1f} секунд перед следующим аккаунтом...")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Критическая ошибка для аккаунта {account['name']}: {e}")
                results.append({
                    'account': account,
                    'success': False,
                    'error': str(e)
                })
        
        # Вывод результатов
        print_registration_results(results)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в register_main: {e}")

def print_registration_results(results):
    """Вывод результатов регистрации"""
    logger.info("\n" + "="*60)
    logger.info("РЕЗУЛЬТАТЫ РЕГИСТРАЦИИ")
    logger.info("="*60)
    
    successful = 0
    for result in results:
        account = result['account']
        if result.get('success'):
            successful += 1
            logger.info(f"✅ {account['name']} - УСПЕШНАЯ РЕГИСТРАЦИЯ")
            logger.info(f"   Email: {account['email']}")
            logger.info("   Статус: Ожидает подтверждения email")
        else:
            logger.info(f"❌ {account['name']} - ОШИБКА РЕГИСТРАЦИИ")
            logger.info(f"   Email: {account['email']}")
            logger.info(f"   Ошибка: {result.get('error', 'Unknown error')}")
    
    logger.info(f"\nИтог регистрации: {successful}/{len(results)} успешных регистраций")
    
    if successful > 0:
        logger.info("\n📧 Для подтверждения email запустите: python confirm_main.py")

if __name__ == "__main__":
    main()
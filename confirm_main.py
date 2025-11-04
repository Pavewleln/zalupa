# confirm_main.py
import logging
import time
import sys
import os

# Добавляем путь к текущей директории для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from account_manager import AccountManager
from email_confirmer import EmailConfirmer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('confirmation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция для подтверждения email"""
    try:
        logger.info("=== ЗАПУСК ПОДТВЕРЖДЕНИЯ EMAIL ===")
        
        # Инициализация менеджеров
        account_manager = AccountManager("accounts.json")
        confirmer = EmailConfirmer(account_manager)
        
        # Получаем аккаунты для подтверждения
        accounts_to_confirm = account_manager.get_unconfirmed_accounts()
        
        if not accounts_to_confirm:
            logger.info("Нет аккаунтов для подтверждения")
            logger.info("Все аккаунты уже подтверждены или не зарегистрированы")
            return
        
        logger.info(f"Найдено {len(accounts_to_confirm)} аккаунтов для подтверждения")
        
        # Обработка аккаунтов
        results = []
        for i, account in enumerate(accounts_to_confirm, 1):
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Аккаунт {i}/{len(accounts_to_confirm)}: {account['name']} ({account['email']})")
                logger.info(f"{'='*50}")
                
                # Подтверждаем email
                max_attempts = account_manager.settings.get('email_check_attempts', 3)
                result = confirmer.process_account_confirmation(account, max_attempts)
                results.append(result)
                
                # Короткая задержка между аккаунтами
                if i < len(accounts_to_confirm):
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f"Критическая ошибка для аккаунта {account['name']}: {e}")
                results.append({
                    'account': account,
                    'success': False,
                    'error': str(e)
                })
        
        # Вывод результатов
        print_confirmation_results(results)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в confirm_main: {e}")

def print_confirmation_results(results):
    """Вывод результатов подтверждения"""
    logger.info("\n" + "="*60)
    logger.info("РЕЗУЛЬТАТЫ ПОДТВЕРЖДЕНИЯ EMAIL")
    logger.info("="*60)
    
    successful = 0
    for result in results:
        account = result['account']
        if result.get('success'):
            successful += 1
            logger.info(f"✅ {account['name']} - EMAIL ПОДТВЕРЖДЕН")
            logger.info(f"   Email: {account['email']}")
            logger.info(f"   Найдено ссылок: {len(result.get('confirmation_links', []))}")
            
            for link_info in result.get('confirmation_links', []):
                logger.info(f"     📧 {link_info['subject']}")
                logger.info(f"     🔗 {link_info['link'][:80]}...")
        else:
            logger.info(f"❌ {account['name']} - ПОДТВЕРЖДЕНИЕ НЕ УДАЛОСЬ")
            logger.info(f"   Email: {account['email']}")
            logger.info(f"   Ошибка: {result.get('error', 'Unknown error')}")
            logger.info(f"   Найдено писем: {result.get('emails_found', 0)}")
    
    logger.info(f"\nИтог подтверждения: {successful}/{len(results)} успешных подтверждений")

if __name__ == "__main__":
    main()
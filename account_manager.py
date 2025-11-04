# account_manager.py
import json
import random
import string
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AccountManager:
    def __init__(self, account_file: str = "accounts.json"):
        self.account_file = account_file
        self.accounts = []
        self.settings = {}
        self.load_accounts()
    
    def load_accounts(self) -> None:
        """Загрузка аккаунтов из файла"""
        try:
            with open(self.account_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.accounts = data.get('accounts', [])
                self.settings = data.get('settings', {})
            
            logger.info(f"Загружено {len(self.accounts)} аккаунтов")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки аккаунтов: {e}")
            self.accounts = []
    
    def get_active_accounts(self) -> List[Dict]:
        """Получение активных аккаунтов"""
        return [acc for acc in self.accounts if acc.get('active', True)]
    
    def get_unregistered_accounts(self) -> List[Dict]:
        """Получение незарегистрированных аккаунтов"""
        return [acc for acc in self.get_active_accounts() if not acc.get('registered', False)]
    
    def get_unconfirmed_accounts(self) -> List[Dict]:
        """Получение аккаунтов без подтверждения почты"""
        return [acc for acc in self.get_active_accounts() if acc.get('registered', True) and not acc.get('email_confirmed', False)]
    
    def get_confirmed_accounts(self) -> List[Dict]:
        """Получение подтвержденных аккаунтов"""
        return [acc for acc in self.get_active_accounts() if acc.get('email_confirmed', False)]
    
    def generate_password(self, length: Optional[int] = None) -> str:
        """Генерация надежного пароля"""
        if length is None:
            length = self.settings.get('password_length', 12)
        
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for _ in range(length))
    
    def update_account(self, email: str, updates: Dict) -> bool:
        """Обновление данных аккаунта"""
        try:
            for account in self.accounts:
                if account['email'] == email:
                    account.update(updates)
                    self.save_accounts()
                    logger.info(f"Аккаунт {email} обновлен")
                    return True
            
            logger.warning(f"Аккаунт {email} не найден")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления аккаунта: {e}")
            return False
    
    def mark_registered(self, email: str, success: bool = True) -> bool:
        """Пометка аккаунта как зарегистрированного"""
        import time
        updates = {
            'registered': success,
            'registration_date': time.time() if success else None
        }
        return self.update_account(email, updates)
    
    def mark_email_confirmed(self, email: str, confirmation_links: List[Dict] = None) -> bool:
        """Пометка аккаунта как подтвержденного по email"""
        updates = {
            'email_confirmed': True,
            'confirmation_links': confirmation_links or []
        }
        return self.update_account(email, updates)
    
    def add_confirmation_links(self, email: str, links: List[Dict]) -> bool:
        """Добавление ссылок подтверждения к аккаунту"""
        try:
            for account in self.accounts:
                if account['email'] == email:
                    current_links = account.get('confirmation_links', [])
                    # Добавляем только новые ссылки
                    for link in links:
                        if link not in current_links:
                            current_links.append(link)
                    account['confirmation_links'] = current_links
                    self.save_accounts()
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка добавления ссылок подтверждения: {e}")
            return False
    
    def add_account(self, account_data: Dict) -> bool:
        """Добавление нового аккаунта"""
        try:
            # Проверка обязательных полей
            required_fields = ['email', 'password', 'name']
            for field in required_fields:
                if field not in account_data:
                    logger.error(f"Отсутствует обязательное поле: {field}")
                    return False
            
            # Генерация пароля если нужно
            if self.settings.get('auto_generate_passwords', False):
                account_data['password'] = self.generate_password()
            
            # Установка значений по умолчанию
            account_data.setdefault('active', True)
            account_data.setdefault('registered', False)
            account_data.setdefault('email_confirmed', False)
            account_data.setdefault('registration_date', None)
            account_data.setdefault('imap_server', 'outlook.office365.com')
            account_data.setdefault('confirmation_links', [])
            account_data.setdefault('notes', '')
            
            self.accounts.append(account_data)
            self.save_accounts()
            logger.info(f"Добавлен новый аккаунт: {account_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления аккаунта: {e}")
            return False
    
    def save_accounts(self) -> None:
        """Сохранение аккаунтов в файл"""
        try:
            data = {
                'accounts': self.accounts,
                'settings': self.settings
            }
            
            with open(self.account_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info("Аккаунты сохранены в файл")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения аккаунтов: {e}")
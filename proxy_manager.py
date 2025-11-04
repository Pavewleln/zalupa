# proxy_manager.py
import json
import random
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxy_file: str = "proxies.json"):
        self.proxy_file = proxy_file
        self.proxies = []
        self.current_index = 0
        self.load_proxies()
    
    def load_proxies(self) -> None:
        """Загрузка прокси из файла"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.proxies = [p for p in data.get('proxies', []) if p.get('active', True)]
                self.settings = data.get('settings', {})
            
            logger.info(f"Загружено {len(self.proxies)} активных прокси")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки прокси: {e}")
            self.proxies = []
    
    def get_proxy(self, proxy_str: Optional[str] = None) -> Dict[str, str]:
        """Получение прокси в формате для requests"""
        if proxy_str:
            return self._parse_proxy_string(proxy_str)
        
        if not self.proxies:
            logger.warning("Нет доступных прокси")
            return {}
        
        # Ротация прокси
        proxy_data = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        return self._format_proxy(proxy_data)
    
    def get_random_proxy(self) -> Dict[str, str]:
        """Получение случайного прокси"""
        if not self.proxies:
            return {}
        
        proxy_data = random.choice(self.proxies)
        return self._format_proxy(proxy_data)
    
    def _parse_proxy_string(self, proxy_str: str) -> Dict[str, str]:
        """Парсинг строки прокси"""
        try:
            parts = proxy_str.split(':')
            if len(parts) == 4:
                host, port, username, password = parts
                proxy_url = f"http://{username}:{password}@{host}:{port}"
                return {'http': proxy_url, 'https': proxy_url}
            else:
                logger.error(f"Неверный формат прокси: {proxy_str}")
                return {}
        except Exception as e:
            logger.error(f"Ошибка парсинга прокси: {e}")
            return {}
    
    def _format_proxy(self, proxy_data: Dict) -> Dict[str, str]:
        """Форматирование прокси данных"""
        try:
            host = proxy_data['host']
            port = proxy_data['port']
            username = proxy_data['username']
            password = proxy_data['password']
            
            proxy_url = f"http://{username}:{password}@{host}:{port}"
            return {'http': proxy_url, 'https': proxy_url}
        except KeyError as e:
            logger.error(f"Отсутствует ключ в данных прокси: {e}")
            return {}
    
    def add_proxy(self, proxy_data: Dict) -> None:
        """Добавление нового прокси"""
        self.proxies.append(proxy_data)
        self.save_proxies()
    
    def save_proxies(self) -> None:
        """Сохранение прокси в файл"""
        try:
            data = {
                'proxies': self.proxies,
                'settings': self.settings
            }
            
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info("Прокси сохранены в файл")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения прокси: {e}")
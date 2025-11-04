# setup_captcha.py
import json
import logging
import os

logger = logging.getLogger(__name__)

def setup_captcha_api_key():
    """Настройка API ключа для 2captcha"""
    
    print("=== НАСТРОЙКА 2CAPTCHA API ===")
    print()
    print("Для работы авторегистратора необходим API ключ от 2captcha.com")
    print()
    print("1. Зарегистрируйтесь на https://2captcha.com/")
    print("2. Пополните баланс (минимум $2-3)")
    print("3. Найдите API ключ в личном кабинете")
    print()
    
    api_key = input("Введите ваш API ключ 2captcha: ").strip()
    
    if not api_key:
        print("❌ API ключ не может быть пустым")
        return False
    
    # Обновляем конфигурацию
    try:
        # Обновляем config.py
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем API ключ в config.py
        new_content = content.replace(
            "'api_key': 'YOUR_API_KEY_HERE'",
            f"'api_key': '{api_key}'"
        )
        
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Обновляем accounts.json
        with open('accounts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'settings' not in data:
            data['settings'] = {}
        
        if 'captcha_service' not in data['settings']:
            data['settings']['captcha_service'] = {}
        
        data['settings']['captcha_service']['api_key'] = api_key
        
        with open('accounts.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✅ API ключ успешно сохранен!")
        print()
        print("Теперь вы можете запустить регистрацию:")
        print("python register_main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения API ключа: {e}")
        return False

if __name__ == "__main__":
    setup_captcha_api_key()
# confirm_main.py
import imaplib
import email
import time
import re
from email.header import decode_header

# Аккаунты для подтверждения (те же что и для регистрации)
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

def check_email_imap(email_addr: str, password: str) -> list:
    """Проверка почты через IMAP"""
    try:
        print(f"Проверка почты {email_addr}...")
        mail = imaplib.IMAP4_SSL("outlook.office365.com")
        mail.login(email_addr, password)
        mail.select("inbox")

        # Ищем все письма
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        
        emails_info = []
        
        # Проверяем последние 10 писем
        for email_id in email_ids[-10:]:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else 'utf-8')
                    
                    email_info = {
                        'subject': subject,
                        'from': msg.get("From"),
                        'date': msg.get("Date")
                    }
                    
                    # Получаем тело письма
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors='ignore')
                                    break
                                except:
                                    continue
                    else:
                        content_type = msg.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body = msg.get_payload(decode=True).decode(errors='ignore')
                            except:
                                pass
                    
                    email_info['body'] = body
                    emails_info.append(email_info)
        
        mail.close()
        mail.logout()
        
        print(f"Найдено {len(emails_info)} писем")
        return emails_info
        
    except Exception as e:
        print(f"Ошибка проверки почты: {e}")
        return []

def extract_confirmation_links(email_body: str) -> list:
    """Извлечение ссылок подтверждения"""
    urls = re.findall(r'https?://[^\s<>"]+', email_body)
    
    confirmation_links = []
    for url in urls:
        if any(keyword in url.lower() for keyword in ['confirm', 'verify', 'activation', 'activate', 'validation', 'etsy']):
            confirmation_links.append(url)
    
    return confirmation_links

def process_account_confirmation(account: dict) -> bool:
    """Обработка подтверждения для одного аккаунта"""
    print(f"\n--- Подтверждение: {account['name']} ---")
    
    for attempt in range(3):
        try:
            print(f"Попытка {attempt + 1}/3...")
            
            # Проверяем почту
            emails = check_email_imap(account['email'], account['password'])
            
            # Ищем ссылки подтверждения
            for email_msg in emails:
                links = extract_confirmation_links(email_msg.get('body', ''))
                for link in links:
                    print(f"✅ Найдена ссылка: {email_msg['subject']}")
                    print(f"🔗 {link}")
                    return True
            
            # Ждем перед следующей попыткой
            if attempt < 2:
                print("Ссылки не найдены, ждем 10 сек...")
                time.sleep(10)
                
        except Exception as e:
            print(f"Ошибка: {e}")
            if attempt < 2:
                time.sleep(10)
    
    print("❌ Ссылки подтверждения не найдены")
    return False

def main():
    """Основная функция"""
    print("=== ПОДТВЕРЖДЕНИЕ EMAIL ===")
    
    results = []
    for account in ACCOUNTS:
        success = process_account_confirmation(account)
        results.append(success)
        
        # Короткая пауза между аккаунтами
        time.sleep(2)
    
    # Итоги
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Подтверждено: {sum(results)}/{len(ACCOUNTS)}")

if __name__ == "__main__":
    main()
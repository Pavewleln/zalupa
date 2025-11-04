# email_confirmer.py
import imaplib
import email
import time
import logging
import re
from email.header import decode_header
from typing import Dict, List, Optional

from config.config import IMAP_CONFIG
from account_manager import AccountManager

logger = logging.getLogger(__name__)

class EmailConfirmer:
    def __init__(self, account_manager: AccountManager):
        self.account_manager = account_manager
    
    def check_email_imap(self, email_addr: str, password: str, imap_server: str = None) -> List[Dict]:
        """Проверка почты через IMAP для подтверждения"""
        try:
            if imap_server is None:
                imap_server = IMAP_CONFIG.get('outlook', 'outlook.office365.com')
            
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_addr, password)
            mail.select("inbox")

            # Ищем все письма (не только непрочитанные)
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
                        
                        from_, encoding = decode_header(msg.get("From"))[0]
                        if isinstance(from_, bytes):
                            from_ = from_.decode(encoding if encoding else 'utf-8')
                        
                        email_info = {
                            'id': email_id.decode(),
                            'subject': subject,
                            'from': from_,
                            'date': msg.get("Date")
                        }
                        
                        # Получаем тело письма
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if content_type == "text/plain" and "attachment" not in content_disposition:
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
            
            return emails_info
            
        except Exception as e:
            logger.error(f"Ошибка при проверке почты {email_addr}: {e}")
            return []
    
    def extract_confirmation_links(self, email_body: str) -> List[str]:
        """Извлечение ссылок подтверждения из тела письма"""
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', email_body)
        
        confirmation_links = []
        for url in urls:
            if any(keyword in url.lower() for keyword in ['confirm', 'verify', 'activation', 'activate', 'validation', 'etsy']):
                confirmation_links.append(url)
        
        return confirmation_links
    
    def process_account_confirmation(self, account: Dict, max_attempts: int = 3) -> Dict:
        """Обработка подтверждения email для одного аккаунта"""
        logger.info(f"Проверка подтверждения для: {account['email']}")
        
        confirmation_links = []
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Попытка {attempt + 1}/{max_attempts} проверки почты...")
                
                # Проверяем почту
                emails = self.check_email_imap(
                    account['email'], 
                    account['password'],
                    account.get('imap_server')
                )
                
                # Ищем ссылки подтверждения
                for email_msg in emails:
                    links = self.extract_confirmation_links(email_msg.get('body', ''))
                    for link in links:
                        link_info = {
                            'subject': email_msg['subject'],
                            'link': link,
                            'found_at': time.time()
                        }
                        if link_info not in confirmation_links:
                            confirmation_links.append(link_info)
                            logger.info(f"Найдена ссылка подтверждения: {email_msg['subject']}")
                
                # Если нашли ссылки, выходим
                if confirmation_links:
                    break
                
                # Ждем перед следующей попыткой
                if attempt < max_attempts - 1:
                    delay = self.account_manager.settings.get('email_check_delay', 10)
                    logger.info(f"Ссылки не найдены, ждем {delay} секунд...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Ошибка при проверке почты (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(10)
        
        # Сохраняем найденные ссылки
        if confirmation_links:
            self.account_manager.add_confirmation_links(account['email'], confirmation_links)
            
            # Помечаем как подтвержденный если нашли ссылки
            self.account_manager.mark_email_confirmed(account['email'], confirmation_links)
            
            return {
                'success': True,
                'account': account,
                'emails_found': len(emails) if 'emails' in locals() else 0,
                'confirmation_links': confirmation_links,
                'email_confirmed': True
            }
        else:
            return {
                'success': False,
                'account': account,
                'error': 'Ссылки подтверждения не найдены',
                'emails_found': len(emails) if 'emails' in locals() else 0,
                'confirmation_links': []
            }
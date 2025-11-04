# config.py
import uuid
from typing import Dict, List

# URL endpoints
URLS = {
    'recaptcha_anchor': 'https://www.google.com/recaptcha/enterprise/anchor',
    'recaptcha_reload': 'https://www.google.com/recaptcha/enterprise/reload',
    'etsy_register': 'https://www.etsy.com/api/v3/ajax/bespoke/member/neu/specs/Join_Neu_Controller',
    'etsy_home': 'https://www.etsy.com/'
}

# reCAPTCHA configuration
RECAPTCHA_CONFIG = {
    'site_key': '6Ldgkr0ZAAAAAGnf08YhMemepXW29Ux9rtJCcBD3',
    'enterprise': True,
    'page_url': 'https://www.etsy.com/'
}

# 2captcha configuration
CAPTCHA_SERVICE_CONFIG = {
    'service': '2captcha',  # или 'anticaptcha'
    'api_key': 'YOUR_API_KEY_HERE',  # Замените на ваш API ключ
    'timeout': 120,
    'polling_interval': 5
}

# Headers templates
HEADERS = {
    'common': {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Ch-Ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    },
    'etsy_register': {
        'Content-Type': 'application/json',
        'Origin': 'https://www.etsy.com',
        'Referer': 'https://www.etsy.com/',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Detected-Locale': 'USD|ru|AU',
        'X-Etsy-Protection': '1'
    }
}

# IMAP settings
IMAP_CONFIG = {
    'outlook': 'outlook.office365.com',
    'gmail': 'imap.gmail.com',
    'yahoo': 'imap.mail.yahoo.com'
}

# Default CSRF token (fallback)
DEFAULT_CSRF_TOKEN = "3:1762247928:UhRO1FtMYcuSRx5Q9peUll12b2SD:18732cb4f75dfd1d226fc1ca03748a300e9347f1c8ee036d995ee96f67461330"
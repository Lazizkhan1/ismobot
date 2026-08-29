import os
from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv('TOKEN')
CHANNEL_ID = int(getenv('CHANNEL_ID', '0'))
GROUP_ID = int(getenv('GROUP_ID', '0'))
ADMIN = int(getenv('ADMIN_ID', '0'))
WEB_SERVER_HOST = getenv('WEB_SERVER_HOST', '0.0.0.0')
WEB_SERVER_PORT = int(getenv('WEB_SERVER_PORT', '8080'))
WEBHOOK_PATH = getenv('WEBHOOK_PATH', '/webhook')
WEBHOOK_SECRET = getenv('WEBHOOK_SECRET', 'secret')
BASE_WEBHOOK_URL = getenv('BASE_WEBHOOK_URL', '')
if not BASE_WEBHOOK_URL and os.getenv('BASE_WEBHOOK_URL'):
    BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
DB_NAME = getenv('DB_NAME', 'ismobot')
DB_USER = getenv('DB_USER', 'postgres')
DB_PASS = getenv('DB_PASS', '123')
DB_HOST = getenv('DB_HOST', 'localhost')  
DB_PORT = int(getenv('DB_PORT', '5432'))
INSTAGRAM_URL = getenv('INSTAGRAM_URL', 'https://instagram.com')
CARD_NUMBER = getenv('CARD_NUMBER', '')
DEFAULT_LANGUAGE = getenv('DEFAULT_LANGUAGE', 'uz')

ORDER_PRICE = int(getenv('ORDER_PRICE', getenv('FAST_DELIVERY', 30000)))
FAST_DELIVERY = ORDER_PRICE
SLOW_DELIVERY = int(getenv('SLOW_DELIVERY', 30000))
OVERFLOW_DISCOUNT_AMOUNT = int(getenv('OVERFLOW_DISCOUNT_AMOUNT', 10000))


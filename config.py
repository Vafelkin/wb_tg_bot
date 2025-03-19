import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройки Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки Wildberries API
WB_API_TOKEN = os.getenv('WB_API_TOKEN')  # Токен для статистики
WB_FEEDBACK_TOKEN = os.getenv('WB_FEEDBACK_TOKEN')  # Токен для отзывов и вопросов
WB_API_BASE_URL = 'https://statistics-api.wildberries.ru'
WB_FEEDBACK_API_URL = 'https://feedbacks-api.wildberries.ru'

# Интервал проверки новых данных (в секундах)
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '1800'))  # 30 минут по умолчанию

# Максимальное количество заказов/продаж в одном ответе API
MAX_ORDERS_PER_REQUEST = int(os.getenv('MAX_ORDERS_PER_REQUEST', '80000'))

# Задержка между запросами при пагинации (в секундах)
PAGINATION_DELAY = int(os.getenv('PAGINATION_DELAY', '1')) 
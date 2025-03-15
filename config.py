import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройки Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки Wildberries API
WB_API_TOKEN = os.getenv('WB_API_TOKEN')
WB_API_BASE_URL = 'https://statistics-api.wildberries.ru'

# Интервал проверки новых заказов (в секундах)
CHECK_INTERVAL = 1800  # 30 минут (так как API обновляется раз в 30 минут)

# Интервал проверки отзывов и вопросов (в секундах)
FEEDBACK_CHECK_INTERVAL = 100  # раз в 100 секунд

# Количество дней для проверки заказов
ORDERS_DAYS_LOOK_BACK = 1  # проверять заказы за последний день

# Максимальное количество заказов в одном ответе API
MAX_ORDERS_PER_REQUEST = 80000

# Задержка между запросами при пагинации (в секундах)
PAGINATION_DELAY = 1 
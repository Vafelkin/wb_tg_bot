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

# Интервал проверки новых заказов (в секундах)
CHECK_INTERVAL = 1800  # 30 минут (так как API обновляется раз в 30 минут)

# Интервал проверки отзывов и вопросов (в секундах)
FEEDBACK_CHECK_INTERVAL = 600  # 10 минут между запросами

# Интервал проверки продаж (в секундах)
SALES_CHECK_INTERVAL = 1800  # 30 минут между запросами (аналогично заказам)

# Количество дней для проверки заказов
ORDERS_DAYS_LOOK_BACK = int(os.getenv('ORDERS_DAYS_LOOK_BACK', 2))  # проверять заказы за последние 2 дня

# Количество дней для проверки продаж
SALES_DAYS_LOOK_BACK = int(os.getenv('SALES_DAYS_LOOK_BACK', 1))  # проверять продажи за последний день

# Максимальное количество заказов в одном ответе API
MAX_ORDERS_PER_REQUEST = 80000

# Задержка между запросами при пагинации (в секундах)
PAGINATION_DELAY = 1 
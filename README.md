# Wildberries Telegram Notifier

Приложение для отслеживания новых заказов с Wildberries и отправки уведомлений в Telegram.

## Возможности

- 🔄 Автоматическая проверка новых заказов
- 📱 Мгновенные уведомления в Telegram
- 🛍 Детальная информация о каждом заказе
- ⚙️ Настраиваемый интервал проверки

## Установка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd wb_telegram_notifier
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Заполните `.env` файл своими данными:
- Получите токен Telegram бота у [@BotFather](https://t.me/BotFather)
- Получите API токен Wildberries в личном кабинете продавца
- Укажите ID чата Telegram для получения уведомлений

## Использование

Запустите приложение командой:
```bash
python main.py
```

## Настройка

- В файле `config.py` вы можете изменить интервал проверки заказов (по умолчанию 5 минут)
- Формат уведомлений можно настроить в функции `format_order_message` в файле `main.py`

## Требования

- Python 3.7+
- Доступ к API Wildberries
- Telegram бот 
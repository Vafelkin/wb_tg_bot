# Telegram бот для мониторинга Wildberries

Бот для отслеживания заказов, выкупов, отзывов и вопросов на маркетплейсе Wildberries с отправкой уведомлений в Telegram.

## Функционал

- 🔔 **Уведомления о новых заказах**
  - Артикул продавца
  - Сумма к оплате
  - Регион доставки
  - Склад
  - Дата заказа

- 💰 **Уведомления о выкупах**
  - Артикул продавца
  - Бренд и название товара
  - Цена розничная
  - Комиссия
  - Сумма к выплате
  - Регион
  - Дата выкупа

- 📝 **Уведомления о новых отзывах и вопросах**
  - Количество новых отзывов
  - Количество новых вопросов

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/nikolay/wb_tg_bot.git
cd wb_tg_bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и заполните необходимые параметры:
```bash
cp .env.example .env
```

## Настройка

### Получение токенов

1. **Telegram Bot Token**
   - Напишите [@BotFather](https://t.me/botfather) в Telegram
   - Используйте команду `/newbot`
   - Следуйте инструкциям для создания бота
   - Скопируйте полученный токен в `.env`

2. **Telegram Chat ID**
   - Напишите [@userinfobot](https://t.me/userinfobot) в Telegram
   - Он покажет ваш ID
   - Для добавления нескольких получателей используйте запятую без пробелов: `123456789,987654321`
   - Скопируйте ID в `.env`

3. **Wildberries API Token (для статистики)**
   - Войдите в [личный кабинет WB](https://suppliers.wildberries.ru/)
   - Перейдите в Настройки → Доступ к API → Статистика
   - Сгенерируйте токен
   - Скопируйте токен в `.env`

4. **Wildberries Feedback Token**
   - В личном кабинете WB
   - Перейдите в Настройки → Доступ к API → Работа с отзывами/вопросами
   - Сгенерируйте токен
   - Скопируйте токен в `.env`

### Настройка интервалов проверки

В файле `.env` можно настроить следующие параметры:

- `CHECK_INTERVAL` - интервал проверки заказов (по умолчанию 1800 сек = 30 мин)
- `SALES_CHECK_INTERVAL` - интервал проверки выкупов (по умолчанию 1800 сек = 30 мин)
- `FEEDBACK_CHECK_INTERVAL` - интервал проверки отзывов (по умолчанию 600 сек = 10 мин)
- `ORDERS_DAYS_LOOK_BACK` - период поиска заказов в прошлом (по умолчанию 2 дня)
- `SALES_DAYS_LOOK_BACK` - период поиска выкупов в прошлом (по умолчанию 2 дня)
- `PAGINATION_DELAY` - задержка между запросами к API при пагинации (по умолчанию 1 сек)

Бот использует таймаут в 30 секунд для API запросов к Wildberries, чтобы избежать зависаний при проблемах с соединением.

## Запуск

### Локальный запуск
```bash
python3 main.py
```

### Запуск как systemd сервис (для Linux серверов)

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/wb-tg-bot.service
```

2. Вставьте следующее содержимое (замените пути на ваши):
```ini
[Unit]
Description=Wildberries Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/wb_tg_bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 /path/to/wb_tg_bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Активируйте и запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wb-tg-bot
sudo systemctl start wb-tg-bot
```

4. Проверьте статус:
```bash
sudo systemctl status wb-tg-bot
```

5. Просмотр логов:
```bash
sudo journalctl -u wb-tg-bot -f
```

## Особенности работы

- Бот отслеживает новые заказы (когда покупатель только заказал товар)
- Отслеживает выкупы (когда покупатель получил и принял товар)
- Проверяет наличие новых отзывов и вопросов
- Отправляет уведомления в указанные Telegram чаты
- Автоматически обрабатывает ошибки и таймауты
- Поддерживает пагинацию при большом количестве данных

## Управление ботом на сервере

- **Проверка статуса**: `sudo systemctl status wb-tg-bot`
- **Перезапуск бота**: `sudo systemctl restart wb-tg-bot`
- **Остановка бота**: `sudo systemctl stop wb-tg-bot`
- **Просмотр логов в реальном времени**: `sudo journalctl -u wb-tg-bot -f`

## Требования

- Python 3.7+
- Доступ к API Wildberries
- Telegram бот
- Доступ к интернету

## Зависимости

- python-telegram-bot
- requests
- python-dotenv
- schedule

## Лицензия

MIT

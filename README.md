# Telegram бот для мониторинга Wildberries

[![Python 3.7+](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-✓-blue.svg)](https://core.telegram.org/bots/api)
[![Wildberries API](https://img.shields.io/badge/Wildberries%20API-✓-purple.svg)](https://suppliers-api.wildberries.ru/)
[![Maintenance](https://img.shields.io/badge/Maintained-yes-green.svg)](https://github.com/Vafelkin/wb_tg_bot/commits/main)
[![Last Commit](https://img.shields.io/github/last-commit/Vafelkin/wb_tg_bot.svg)](https://github.com/Vafelkin/wb_tg_bot/commits/main)
[![Code style: black](https://img.shields.io/badge/code%20style-standard-black.svg)](https://github.com/psf/black)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/BotFather)

Бот для отслеживания новых заказов, выкупов, отзывов и вопросов на маркетплейсе Wildberries с отправкой уведомлений в Telegram.

## 📋 Функционал

- 🔔 **Уведомления о новых заказах**
  - Артикул продавца
  - Сумма к оплате (что заплатил покупатель и что получит продавец)
  - Регион доставки и информация о складе
  - Дата и время заказа

- 💰 **Уведомления о выкупах**
  - Артикул продавца
  - Бренд и название товара
  - Цена розничная
  - Комиссия маркетплейса
  - Сумма к выплате продавцу
  - Регион доставки
  - Дата и время выкупа

- 📝 **Уведомления о новых отзывах и вопросах**
  - Количество новых отзывов
  - Количество новых вопросов
  - Напоминание о необходимости проверить личный кабинет WB

## ✨ Особенности работы

- **Только новые данные**: Бот отслеживает только новые заказы, выкупы, отзывы и вопросы, избегая дублирования уведомлений
- **Умное отслеживание**: При первом запуске бот сканирует историю заказов и продаж, но не спамит уведомлениями о старых событиях
- **Оптимизированные интервалы**: Проверка данных происходит с интервалами, учитывающими частоту обновления API Wildberries
- **Надежность**: Автоматическая обработка ошибок и повторное подключение при сбоях API
- **Пагинация**: Корректная обработка больших объемов данных с использованием пагинации
- **Запуск как сервис**: Возможность запуска в качестве системного сервиса для непрерывной работы

## 🚀 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/wb_tg_bot.git
cd wb_tg_bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
   - На Windows:
   ```bash
   venv\Scripts\activate
   ```
   - На Linux/macOS:
   ```bash
   source venv/bin/activate
   ```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Создайте файл `.env` на основе `.env.example` и заполните необходимые параметры:
```bash
cp .env.example .env
```

## ⚙️ Настройка

### 🔑 Получение токенов

1. **Telegram Bot Token**
   - Напишите [@BotFather](https://t.me/botfather) в Telegram
   - Используйте команду `/newbot`
   - Следуйте инструкциям для создания бота
   - Скопируйте полученный токен в `.env` параметр `TELEGRAM_BOT_TOKEN`

2. **Telegram Chat ID**
   - Напишите [@userinfobot](https://t.me/userinfobot) в Telegram
   - Он покажет ваш ID
   - Скопируйте ID в `.env` параметр `TELEGRAM_CHAT_ID`
   - Для отправки уведомлений нескольким получателям укажите ID через запятую без пробелов

3. **Wildberries API Token (для статистики)**
   - Войдите в [личный кабинет WB](https://suppliers.wildberries.ru/)
   - Перейдите в Настройки → Доступ к API → Статистика
   - Сгенерируйте токен
   - Скопируйте токен в `.env` параметр `WB_API_TOKEN`

4. **Wildberries Feedback Token**
   - В личном кабинете WB
   - Перейдите в Настройки → Доступ к API → Работа с отзывами/вопросами
   - Сгенерируйте токен
   - Скопируйте токен в `.env` параметр `WB_FEEDBACK_TOKEN`

### ⏱️ Настройка интервалов проверки

В файле `.env` можно настроить следующие параметры:

- **CHECK_INTERVAL** - интервал проверки заказов (по умолчанию 1800 сек = 30 мин)
- **SALES_CHECK_INTERVAL** - интервал проверки выкупов (по умолчанию 1800 сек = 30 мин)
- **FEEDBACK_CHECK_INTERVAL** - интервал проверки отзывов (по умолчанию 1800 сек = 30 мин)

### 📅 Настройка исторических данных

Эти параметры влияют только на первый запуск бота и определяют, за какой период будет собрана история существующих заказов и продаж:

- **ORDERS_DAYS_LOOK_BACK** - Период сбора истории заказов при первом запуске (по умолчанию 2 дня)
  - Больше значение = больше памяти использует бот
  - Меньше значение = риск получить уведомления о недавних (но старых) заказах

- **SALES_DAYS_LOOK_BACK** - Период сбора истории продаж при первом запуске (по умолчанию 2 дня)
  - Работает аналогично параметру для заказов

## 🖥️ Запуск

### Локальный запуск
```bash
python main.py
```

### Запуск как systemd сервис (для Linux серверов)

1. Создайте файл конфигурации сервиса `wb-tg-bot.service` в директории с ботом или скопируйте имеющийся.

2. Отредактируйте пути и имя пользователя в файле:
```ini
[Unit]
Description=Wildberries Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/wb_tg_bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/path/to/venv/bin/python /path/to/wb_tg_bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Скопируйте файл сервиса в системную директорию:
```bash
sudo cp wb-tg-bot.service /etc/systemd/system/
```

4. Активируйте и запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wb-tg-bot
sudo systemctl start wb-tg-bot
```

5. Проверьте статус:
```bash
sudo systemctl status wb-tg-bot
```

6. Просмотр логов:
```bash
sudo journalctl -u wb-tg-bot -f
```

### Управление сервисом

- **Остановка**: `sudo systemctl stop wb-tg-bot`
- **Перезапуск**: `sudo systemctl restart wb-tg-bot`
- **Отключение автозапуска**: `sudo systemctl disable wb-tg-bot`

## 💻 Требования

- Python 3.7+
- Доступ к API Wildberries
- Telegram бот
- Доступ к интернету

## 📦 Зависимости

- python-telegram-bot
- requests
- python-dotenv
- schedule

## 📄 Лицензия

MIT

## 📧 Поддержка

Если у вас возникли вопросы или предложения по улучшению бота, пожалуйста, создайте issue в репозитории проекта.

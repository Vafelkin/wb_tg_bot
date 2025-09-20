# 🤖 Wildberries Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org)

Бот для мониторинга заказов, выкупов, отзывов и вопросов на маркетплейсе Wildberries с отправкой уведомлений в Telegram.

## 🌟 Возможности

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

- 🎮 **Интерактивный интерфейс**
  - Inline-кнопки для удобной навигации
  - Проверка статуса API
  - Внеплановая проверка данных
  - Тестовые уведомления

## 📋 Требования

- Python 3.10+
- Доступ к API Wildberries
- Telegram бот
- Доступ к интернету

## 🚀 Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/Vafelkin/wb_tg_bot.git
cd wb_tg_bot
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации
```bash
cp .env.example .env
```

Отредактируйте файл `.env` и заполните необходимые параметры:

```env
# Telegram настройки
TELEGRAM_BOT_TOKEN=ваш_токен_telegram_бота
TELEGRAM_CHAT_ID=ваш_id_чата

# Wildberries API токены
WB_API_TOKEN=ваш_токен_api_статистики
WB_FEEDBACK_TOKEN=ваш_токен_api_отзывов

# Настройки интервалов (опционально)
CHECK_INTERVAL=1800  # Интервал проверки в секундах (30 минут)
```

## 🔧 Получение токенов

### Telegram Bot Token
1. Напишите [@BotFather](https://t.me/botfather) в Telegram
2. Используйте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

### Telegram Chat ID
1. Напишите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Он покажет ваш ID
3. Скопируйте ID в `.env`

### Wildberries API Token (для статистики)
1. Войдите в [личный кабинет WB](https://suppliers.wildberries.ru/)
2. Перейдите в Настройки → Доступ к API → Статистика
3. Сгенерируйте токен
4. Скопируйте токен в `.env`

### Wildberries Feedback Token
1. В личном кабинете WB
2. Перейдите в Настройки → Доступ к API → Работа с отзывами/вопросами
3. Сгенерируйте токен
4. Скопируйте токен в `.env`

## 🎮 Использование

### Локальный запуск
```bash
python3 main.py
```

### Запуск как systemd сервис (Linux)

1. **Создание файла сервиса:**
```bash
sudo nano /etc/systemd/system/wb-tg-bot.service
```

2. **Содержимое файла сервиса:**
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

3. **Активация и запуск сервиса:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable wb-tg-bot
sudo systemctl start wb-tg-bot
```

4. **Проверка статуса:**
```bash
sudo systemctl status wb-tg-bot
```

5. **Просмотр логов:**
```bash
sudo journalctl -u wb-tg-bot -f
```

## 📲 Команды Telegram бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и показ основного меню |
| `/status` | Проверка состояния API Wildberries |
| `/test` | Отправка тестовых уведомлений |
| `/help` | Показ справки |

## 🎯 Интерфейс бота

Бот предоставляет удобный интерфейс с кнопками:

- **📊 Статус API** - проверка работоспособности API
- **🔍 Проверить сейчас** - внеплановая проверка данных
- **❓ Помощь** - показ справки
- **🧪 Тест** - отправка тестовых уведомлений

## ⚙️ Настройка интервалов

В файле `.env` можно настроить следующие параметры:

- `CHECK_INTERVAL` - интервал проверки заказов (по умолчанию 1800 сек = 30 мин)
- `MAX_ORDERS_PER_REQUEST` - максимальное количество записей в одном запросе (по умолчанию 80000)
- `PAGINATION_DELAY` - задержка между запросами при пагинации (по умолчанию 1 сек)

## 🔒 Безопасность

- Аутентификация пользователей по ID чата
- Обработка ошибок API Wildberries
- Хранение токенов в файле окружения `.env`
- Контроль доступа к функциям бота

## 📊 Особенности работы

- Бот отслеживает новые заказы (когда покупатель только заказал товар)
- Отслеживает выкупы (когда покупатель получил и принял товар)
- Проверяет наличие новых отзывов и вопросов
- Отправляет уведомления в указанные Telegram чаты
- Автоматически обрабатывает ошибки и таймауты
- Поддерживает пагинацию при большом количестве данных
- Использует только FBO fulfillment режим

## 🏗️ Структура проекта

```
wb_tg_bot/
├── main.py              # Основной файл бота
├── config.py            # Загрузка конфигурации
├── .env.example         # Пример файла окружения
├── requirements.txt     # Зависимости проекта
├── wb-tg-bot.service    # Файл службы systemd
├── README.md            # Документация
└── LICENSE              # Лицензия MIT
```

## 🔄 Обновление

Для обновления бота:

```bash
git pull
pip install -r requirements.txt
sudo systemctl restart wb-tg-bot.service  # Если запущен как сервис
```

## 🐛 Устранение неполадок

### Проблема: Rate Limiting (429 ошибки)
**Решение**: Увеличить интервалы между запросами в `.env`:
```env
PAGINATION_DELAY=2  # Увеличить задержку
CHECK_INTERVAL=3600  # Увеличить интервал проверки
```

### Проблема: Бот не отвечает
**Решение**: Проверить статус сервиса:
```bash
sudo systemctl status wb-tg-bot
sudo journalctl -u wb-tg-bot --since "1 hour ago"
```

### Проблема: Не приходят уведомления
**Решение**: 
1. Проверить корректность токенов в `.env`
2. Убедиться, что Chat ID указан правильно
3. Проверить статус API через команду `/status`

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для получения дополнительной информации.

## 🤝 Вклад в проект

Вклады приветствуются! Пожалуйста, не стесняйтесь создавать issues или pull-запросы.

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [Issues](https://github.com/Vafelkin/wb_tg_bot/issues)
2. Создайте новый Issue с подробным описанием проблемы
3. Приложите логи (без токенов!)

---

**Сделано с ❤️ для продавцов Wildberries**

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/Vafelkin/wb_tg_bot)
[![Telegram](https://img.shields.io/badge/Telegram-@BotFather-blue.svg)](https://t.me/botfather)
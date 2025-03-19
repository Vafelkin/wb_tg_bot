# Wildberries Telegram Bot 🤖

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-API-32AFED.svg)](https://core.telegram.org/bots/api)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Wildberries](https://img.shields.io/badge/Wildberries-API-E539A9.svg)](https://openapi.wb.ru/)

Бот для мониторинга статистики, продаж и отзывов магазина на Wildberries с отправкой уведомлений в Telegram. С этим ботом вы всегда будете в курсе новых заказов, продаж и отзывов о ваших товарах!

## 🌟 Возможности

- 📦 **Мониторинг новых заказов** - отслеживание заказов в реальном времени
- 💰 **Мониторинг продаж (выкупов)** - уведомления о новых выкупах
- ⭐ **Мониторинг отзывов и вопросов** - уведомления о новых отзывах и вопросах
- 📊 **Проверка состояния API** - проверка работоспособности API Wildberries
- 🔍 **Внеплановая проверка** - возможность проверить наличие новых данных в любой момент
- 🧪 **Тестовые уведомления** - отправка тестовых уведомлений разных типов
- 🚀 **Удобный интерфейс** - интуитивно понятные кнопки и навигация

## 📋 Требования

- Python 3.10 или выше
- Токены API Wildberries
- Токен Telegram Bot API

## 🚀 Установка

1. **Клонирование репозитория**

```bash
git clone https://github.com/yourusername/wb_tg_bot.git
cd wb_tg_bot
```

2. **Создание виртуального окружения**

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate  # Для Windows
```

3. **Установка зависимостей**

```bash
pip install -r requirements.txt
```

4. **Настройка конфигурации**

```bash
cp .env.example .env
```

Откройте файл `.env` и заполните необходимые параметры:

```
TELEGRAM_BOT_TOKEN=ваш_токен_telegram_бота
TELEGRAM_CHAT_ID=ваш_id_чата
WB_API_TOKEN=ваш_токен_api_статистики
WB_FEEDBACK_TOKEN=ваш_токен_api_отзывов
```

## 🔧 Использование

### Запуск бота вручную

```bash
python main.py
```

### Запуск как системный сервис (Linux)

1. Отредактируйте файл `wb-tg-bot.service`, указав правильные пути

2. Копируйте файл сервиса в системную директорию:

```bash
sudo cp wb-tg-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

3. Включите и запустите сервис:

```bash
sudo systemctl enable wb-tg-bot.service
sudo systemctl start wb-tg-bot.service
```

4. Проверьте статус:

```bash
sudo systemctl status wb-tg-bot.service
```

## 📲 Команды Telegram бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и показ основного меню |
| `/status` | Проверка состояния API Wildberries |
| `/test` | Отправка тестовых уведомлений |
| `/help` | Показ справки |

## 🎮 Интерфейс бота

Бот предоставляет удобный интерфейс с кнопками:

- **📊 Статус API** - проверка работоспособности API
- **🔍 Проверить сейчас** - внеплановая проверка данных
- **❓ Помощь** - показ справки
- **🧪 Тест** - отправка тестовых уведомлений

## 🔒 Безопасность

- Аутентификация пользователей по ID чата
- Обработка ошибок API Wildberries
- Хранение токенов в файле окружения `.env`

## 💼 Структура проекта

```
wb_tg_bot/
├── main.py          # Основной файл бота
├── config.py        # Загрузка конфигурации
├── .env.example     # Пример файла окружения
├── requirements.txt # Зависимости проекта
└── wb-tg-bot.service # Файл службы systemd
```

## 🔄 Обновление

Для обновления бота:

```bash
git pull
pip install -r requirements.txt
sudo systemctl restart wb-tg-bot.service  # Если запущен как сервис
```

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для получения дополнительной информации.

## 🤝 Вклад в проект

Вклады приветствуются! Пожалуйста, не стесняйтесь создавать issues или pull-запросы.

---

Made with ❤️ for Wildberries sellers

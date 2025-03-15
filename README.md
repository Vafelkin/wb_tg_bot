# Wildberries Telegram Notifier 🤖

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot_API-blue?style=flat-square&logo=telegram)](https://core.telegram.org/bots/api)
[![Wildberries](https://img.shields.io/badge/Wildberries-API-purple?style=flat-square)](https://openapi.wb.ru/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=flat-square)](https://github.com/Vafelkin/wb_tg_bot/graphs/commit-activity)

Бот для мониторинга новых заказов с Wildberries и отправки уведомлений в Telegram. Получайте мгновенные уведомления о новых заказах прямо в ваш телефон! 📱

## ✨ Возможности

- 🔄 Автоматическая проверка новых заказов каждые 30 минут
- 📱 Мгновенные уведомления в Telegram для нескольких получателей
- 💰 Детальная информация о ценах (сумма заказа, скидки, ваш доход)
- 📍 Точная информация о местоположении (регион, округ, склад)
- ⚡️ Быстрая обработка данных и защита от дублей
- 🔐 Безопасное хранение конфиденциальных данных
- 🚀 Уведомления о запуске и остановке бота

## 🛠 Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/Vafelkin/wb_tg_bot.git
cd wb_tg_bot
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте конфигурацию:**
   - Создайте файл `.env` на основе `.env.example`
   - Заполните необходимые данные:
     ```env
     TELEGRAM_BOT_TOKEN=ваш_токен_бота
     TELEGRAM_CHAT_ID=ваш_id,id_других_получателей
     WB_API_TOKEN=ваш_токен_вб_апи
     ```

## 🚀 Использование

Запустите бота командой:
```bash
python main.py
```

### 📝 Формат уведомлений

Каждое уведомление содержит:
- 📦 Артикул продавца
- 💳 Сумму, которую заплатил покупатель
- 💰 Сумму вашего дохода
- 💵 Цену со скидкой
- 📍 Регион и федеральный округ
- 🏪 Название и тип склада
- 📅 Дату и время заказа

## ⚙️ Настройка

В файле `config.py` можно настроить:
- ⏱ Интервал проверки заказов (по умолчанию 30 минут)
- 📅 Период просмотра заказов
- 📊 Максимальное количество заказов в запросе
- ⏲ Задержку между запросами при пагинации

## 🔧 Требования

- 🐍 Python 3.7+
- 🌐 Доступ к API Wildberries
- 🤖 Telegram бот

## 📝 Лицензия

MIT License - делайте с кодом что хотите! 

## 🤝 Поддержка

Если у вас есть вопросы или предложения, создавайте [Issue](https://github.com/Vafelkin/wb_tg_bot/issues) или делайте Pull Request! 
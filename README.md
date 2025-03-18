# Telegram бот для мониторинга Wildberries

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Wildberries](https://img.shields.io/badge/Wildberries-API-purple.svg)](https://suppliers.wildberries.ru/)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![Last Commit](https://img.shields.io/github/last-commit/Vafelkin/wb_tg_bot)](https://github.com/Vafelkin/wb_tg_bot/commits/main)

Автоматический бот для отслеживания активности магазина на маркетплейсе Wildberries с мгновенными уведомлениями в Telegram. Получайте информацию о новых заказах, выкупах, отзывах и вопросах в режиме реального времени.

> **Моментальные уведомления о новых заказах и выкупах**  
> **Автоматическое отслеживание отзывов и вопросов**  
> **Простая установка и настройка**  
> **Поддержка работы как системный сервис**

<p align="center">
  <img src="https://user-images.githubusercontent.com/99164769/222405305-d0d7954f-f9ed-4e35-89ea-a555ec168eb3.png" alt="WB Bot Preview" width="600">
</p>

## Функционал

<p align="center">
  <img src="https://user-images.githubusercontent.com/99164769/222407389-6a28f7df-6711-4f1b-b413-39629dc9f5c7.jpg" alt="Notifications Example" width="300">
</p>

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

## Быстрый старт

```bash
# Клонировать репозиторий
git clone https://github.com/nikolay/wb_tg_bot.git

# Перейти в директорию проекта
cd wb_tg_bot

# Установить зависимости
pip install -r requirements.txt

# Создать и настроить .env файл
cp .env.example .env
nano .env  # Заполните необходимые параметры

# Запустить бота
python3 main.py
```

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

## Часто задаваемые вопросы (FAQ)

<details>
<summary>❓ Как изменить периодичность проверки?</summary>
<p>

Для изменения интервалов проверки откройте файл `.env` и измените соответствующие параметры:
- `CHECK_INTERVAL` - для заказов
- `SALES_CHECK_INTERVAL` - для выкупов
- `FEEDBACK_CHECK_INTERVAL` - для отзывов и вопросов

Значения указываются в секундах.
</p>
</details>

<details>
<summary>❓ Почему бот не обнаруживает новые заказы?</summary>
<p>

Убедитесь, что:
1. API токен корректный и не просрочен
2. В магазине действительно появились новые заказы
3. Прошло достаточно времени (API WB обновляется примерно раз в 30 минут)
4. Проверьте логи командой `sudo journalctl -u wb-tg-bot -f` (для systemd)
</p>
</details>

<details>
<summary>❓ Как получать уведомления на несколько Telegram аккаунтов?</summary>
<p>

В файле `.env` укажите несколько Chat ID через запятую в параметре `TELEGRAM_CHAT_ID`:
```
TELEGRAM_CHAT_ID=123456789,987654321
```
</p>
</details>

<details>
<summary>❓ Как обновить бота?</summary>
<p>

```bash
# Переходим в директорию проекта
cd wb_tg_bot

# Получаем последние обновления
git pull

# Перезапускаем сервис (если используется systemd)
sudo systemctl restart wb-tg-bot
```
</p>
</details>

## Контакты / Обратная связь

Если у вас возникли вопросы или предложения по улучшению бота:
- 🐞 [Создать Issue](https://github.com/Vafelkin/wb_tg_bot/issues)
- 🔄 [Сделать Pull Request](https://github.com/Vafelkin/wb_tg_bot/pulls)

---

<p align="center">
Made with ❤️ for Wildberries sellers
</p>

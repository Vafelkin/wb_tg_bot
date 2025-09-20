import requests
import asyncio  # Перемещено в начало файла
import schedule
import time
import signal
import sys
import traceback  # Добавляем для печати полного стека исключения
import json  # Добавляем для работы с тестовыми данными
from datetime import datetime, timedelta, timezone
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WB_API_TOKEN,
    WB_FEEDBACK_TOKEN,
    WB_API_BASE_URL,
    WB_FEEDBACK_API_URL,
    CHECK_INTERVAL,
    MAX_ORDERS_PER_REQUEST,
    PAGINATION_DELAY
)

# Функция для улучшенного логирования
def log(message):
    """Функция для логирования с временной меткой"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {message}")

def get_moscow_time():
    """Возвращает текущее московское время (UTC+3)"""
    return datetime.now(timezone.utc) + timedelta(hours=3)

class WildberriesAPI:
    def __init__(self, stats_token, feedback_token):
        log("🔧 Инициализация WildberriesAPI")
        self.stats_token = stats_token
        self.feedback_token = feedback_token
        self.stats_headers = {'Authorization': stats_token}
        self.feedback_headers = {'Authorization': f'Bearer {feedback_token}'}
        self._last_order_time = datetime.now(timezone.utc)
        self._last_sales_time = datetime.now(timezone.utc)
        self._last_feedback_check = datetime.now(timezone.utc)
        self._processed_orders = set()  # Множество для хранения обработанных srid
        self._processed_sales = set()   # Множество для хранения обработанных saleID
        
        # Проверяем валидность токенов
        if not stats_token or len(stats_token) < 10:
            log("⚠️ Предупреждение: токен API статистики отсутствует или слишком короткий")
        if not feedback_token or len(feedback_token) < 10:
            log("⚠️ Предупреждение: токен API отзывов отсутствует или слишком короткий")
            
        log("✅ WildberriesAPI инициализирован")
    
    def _parse_date(self, date_str):
        """Парсинг даты из API с поддержкой разных форматов"""
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # С миллисекундами
            '%Y-%m-%dT%H:%M:%S',      # Без миллисекунд
            '%Y-%m-%dT%H:%M:%SZ'      # С Z, но без миллисекунд
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # Если ни один формат не подошел, логируем ошибку и возвращаем текущее время
        log(f"⚠️ Неподдерживаемый формат даты: {date_str}. Используем текущее время.")
        return datetime.now()
    
    def get_new_orders(self):
        """Получение новых заказов с Wildberries с поддержкой пагинации"""
        log(f"🔄 Получение новых заказов с {self._last_order_time.strftime('%Y-%m-%dT%H:%M:%S')}")
        all_orders = []
        next_date_from = self._last_order_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        try:
            while True:
                try:
                    url = f"{WB_API_BASE_URL}/api/v1/supplier/orders"
                    log(f"🔄 Запрос заказов: {url} с dateFrom={next_date_from}")
                    
                    response = requests.get(
                        url,
                        headers=self.stats_headers,
                        params={
                            'dateFrom': next_date_from,
                            'flag': 0  # 0 - новые заказы
                        },
                        timeout=30  # Добавляем таймаут
                    )
                    
                    # Проверяем код ответа
                    response.raise_for_status()
                    
                    # Получаем данные
                    orders = response.json()
                    log(f"📦 Получено {len(orders)} заказов от API")
                    
                    # Если нет заказов, прерываем цикл
                    if not orders:
                        break
                    
                    # Добавляем только необработанные заказы
                    new_orders = [
                        order for order in orders 
                        if order.get('srid') not in self._processed_orders
                    ]
                    log(f"📬 Найдено {len(new_orders)} новых заказов")
                    all_orders.extend(new_orders)
                    
                    # Обновляем множество обработанных заказов
                    self._processed_orders.update(order.get('srid') for order in new_orders)
                    
                    # Если получили меньше максимального количества, значит это последняя страница
                    if len(orders) < MAX_ORDERS_PER_REQUEST:
                        break
                        
                    # Берем дату последнего заказа для следующего запроса
                    if orders:
                        next_date_from = orders[-1]['lastChangeDate']
                        log(f"🔄 Следующий запрос с dateFrom={next_date_from}")
                    
                    # Добавляем задержку между запросами
                    log(f"⏱ Ожидание {PAGINATION_DELAY} сек перед следующим запросом")
                    time.sleep(PAGINATION_DELAY)
                    
                except requests.exceptions.HTTPError as e:
                    log(f"❌ Ошибка HTTP при получении заказов: {e}")
                    if e.response.status_code == 401:
                        log("🔑 Возможно, токен устарел или неверный")
                    break
                except requests.exceptions.Timeout as e:
                    log(f"⏱ Превышено время ожидания запроса: {e}")
                    break
                except requests.exceptions.RequestException as e:
                    log(f"❌ Ошибка при получении заказов: {e}")
                    break
                except Exception as e:
                    log(f"❌ Неожиданная ошибка при получении заказов: {e}")
                    break
        finally:
            # Обновляем время последней проверенного заказа на текущее время
            self._last_order_time = datetime.now(timezone.utc)
            log(f"⏱ Время последней проверки заказов обновлено: {self._last_order_time.strftime('%Y-%m-%dT%H:%M:%S')}")
            
        return all_orders

    def check_new_feedbacks(self):
        """Проверка наличия новых отзывов и вопросов"""
        log(f"🔄 Проверка отзывов с {self._last_feedback_check.strftime('%Y-%m-%dT%H:%M:%S')}")
        
        try:
            url = f"{WB_FEEDBACK_API_URL}/api/v1/new-feedbacks-questions"
            log(f"🔄 Запрос отзывов: {url}")
            
            response = requests.get(url, headers=self.feedback_headers, timeout=30)
            
            # Проверяем код ответа
            response.raise_for_status()
            
            result = response.json()
            log(f"📊 Получен ответ по отзывам: {result}")

            # Проверяем наличие ошибок
            if result.get('error'):
                log(f"❌ Ошибка при проверке отзывов: {result.get('errorText')}")
                if result.get('additionalErrors'):
                    log(f"❌ Дополнительные ошибки: {', '.join(result['additionalErrors'])}")
                return None

            # Получаем данные из ответа
            data = result.get('data', {})
            
            # Форматируем информацию о новых отзывах и вопросах
            feedback_info = {
                'has_new_feedbacks': data.get('hasNewFeedbacks', False),
                'has_new_questions': data.get('hasNewQuestions', False),
                'feedbacks_count': data.get('feedbacksCount', 0),
                'questions_count': data.get('questionsCount', 0)
            }
            
            log(f"📊 Результат проверки отзывов: {feedback_info}")
            
            # Обновляем время последней проверки
            self._last_feedback_check = datetime.now(timezone.utc)
            log(f"⏱ Время последней проверки отзывов обновлено: {self._last_feedback_check.strftime('%Y-%m-%dT%H:%M:%S')}")
            
            return feedback_info

        except requests.exceptions.HTTPError as e:
            log(f"❌ Ошибка HTTP при проверке отзывов: {e}")
            if e.response.status_code == 401:
                log("🔑 Возможно, токен устарел или неверный")
            return None
        except requests.exceptions.Timeout as e:
            log(f"⏱ Превышено время ожидания запроса отзывов: {e}")
            return None
        except requests.exceptions.RequestException as e:
            log(f"❌ Ошибка при проверке отзывов и вопросов: {e}")
            return None
        except Exception as e:
            log(f"❌ Неожиданная ошибка при проверке отзывов: {e}")
            return None

    def get_sales(self):
        """Получение данных о новых продажах с Wildberries с поддержкой пагинации"""
        log(f"🔄 Получение новых продаж с {self._last_sales_time.strftime('%Y-%m-%dT%H:%M:%S')}")
        all_sales = []
        date_from = self._last_sales_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        try:
            while True:
                try:
                    url = f"{WB_API_BASE_URL}/api/v1/supplier/sales"
                    log(f"🔄 Запрос продаж: {url} с dateFrom={date_from}")
                    
                    response = requests.get(
                        url,
                        headers=self.stats_headers,
                        params={
                            'dateFrom': date_from,
                            'flag': 0  # 0 - все продажи
                        },
                        timeout=30  # Таймаут 30 секунд
                    )
                    
                    # Проверяем код ответа
                    response.raise_for_status()
                    
                    # Получаем данные
                    sales = response.json()
                    log(f"📦 Получено {len(sales)} продаж от API")
                    
                    # Если нет продаж, прерываем цикл
                    if not sales:
                        break
                    
                    # Добавляем только необработанные продажи
                    new_sales = [
                        sale for sale in sales 
                        if sale.get('saleID') not in self._processed_sales
                    ]
                    log(f"📬 Найдено {len(new_sales)} новых продаж")
                    all_sales.extend(new_sales)
                    
                    # Обновляем множество обработанных продаж
                    self._processed_sales.update(sale.get('saleID') for sale in new_sales if sale.get('saleID'))
                    
                    # Если получили меньше максимального количества, значит это последняя страница
                    if len(sales) < MAX_ORDERS_PER_REQUEST:
                        break
                        
                    # Берем дату последней продажи для следующего запроса
                    if sales:
                        date_from = sales[-1]['lastChangeDate']
                        log(f"🔄 Следующий запрос с dateFrom={date_from}")
                    
                    # Добавляем задержку между запросами
                    log(f"⏱ Ожидание {PAGINATION_DELAY} сек перед следующим запросом")
                    time.sleep(PAGINATION_DELAY)
                    
                except requests.exceptions.HTTPError as e:
                    log(f"❌ Ошибка HTTP при получении продаж: {e}")
                    if e.response.status_code == 401:
                        log("🔑 Возможно, токен устарел или неверный")
                    break
                except requests.exceptions.Timeout:
                    log("❌ Превышено время ожидания ответа от сервера (таймаут).")
                    break
                except requests.exceptions.ConnectionError:
                    log("❌ Ошибка соединения с сервером.")
                    break
                except requests.exceptions.RequestException as e:
                    log(f"❌ Ошибка при получении продаж: {e}")
                    break
                except Exception as e:
                    log(f"❌ Неожиданная ошибка при получении продаж: {e}")
                    break
        finally:
            # Обновляем время последней проверки продаж на текущее время
            self._last_sales_time = datetime.now(timezone.utc)
            log(f"⏱ Время последней проверки продаж обновлено: {self._last_sales_time.strftime('%Y-%m-%dT%H:%M:%S')}")
            
        return all_sales

    def check_api_status(self):
        """Проверка работоспособности API"""
        log("🔍 Запуск проверки API")
        results = {}
        
        # Проверка API статистики
        try:
            log("🔄 Проверка API статистики...")
            url = f"{WB_API_BASE_URL}/api/v1/supplier/orders"
            date_from = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            log(f"🔤 URL запроса: {url}")
            log(f"🔤 Параметры: dateFrom={date_from}, flag=0")
            log(f"🔤 Заголовки: Authorization={self.stats_token[:10]}...")
            
            start_time = datetime.now()
            response = requests.get(
                url,
                headers=self.stats_headers,
                params={
                    'dateFrom': date_from,
                    'flag': 0
                },
                timeout=10
            )
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            log(f"📊 Статус ответа API статистики: {response.status_code}")
            log(f"⏱ Время ответа: {elapsed_time:.2f} сек")
            
            # Проверяем содержимое ответа
            try:
                response_data = response.json()
                log(f"📋 Количество полученных записей: {len(response_data) if isinstance(response_data, list) else 'Не массив'}")
            except ValueError:
                log("❌ Ответ не содержит валидного JSON")
            
            # Если ответ не 200, проверяем содержимое на наличие ошибок
            if response.status_code != 200:
                log(f"⚠️ Код ответа не 200. Содержимое: {response.text[:200]}...")
            
            results['statistics_api'] = {
                'status': 'OK' if response.status_code == 200 else 'ERROR',
                'code': response.status_code,
                'response_time': f"{elapsed_time:.2f} сек",
                'data_received': True if response.status_code == 200 and response.text else False
            }
        except requests.exceptions.Timeout:
            log("⏱ Тайм-аут при проверке API статистики")
            results['statistics_api'] = {
                'status': 'ERROR',
                'error': "Тайм-аут запроса (превышено время ожидания)"
            }
        except requests.exceptions.ConnectionError:
            log("🌐 Ошибка соединения при проверке API статистики")
            results['statistics_api'] = {
                'status': 'ERROR',
                'error': "Ошибка соединения с сервером"
            }
        except Exception as e:
            log(f"❌ Ошибка при проверке API статистики: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            results['statistics_api'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # Проверка API отзывов
        try:
            log("🔄 Проверка API отзывов...")
            url = f"{WB_FEEDBACK_API_URL}/api/v1/new-feedbacks-questions"
            log(f"🔤 URL запроса: {url}")
            log(f"🔤 Заголовки: Authorization=Bearer {self.feedback_token[:10]}...")
            
            start_time = datetime.now()
            response = requests.get(url, headers=self.feedback_headers, timeout=10)
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            log(f"📊 Статус ответа API отзывов: {response.status_code}")
            log(f"⏱ Время ответа: {elapsed_time:.2f} сек")
            
            # Проверяем содержимое ответа
            try:
                response_data = response.json()
                error = response_data.get('error', False)
                if error:
                    log(f"⚠️ API вернул ошибку: {response_data.get('errorText')}")
                    additional_errors = response_data.get('additionalErrors', [])
                    if additional_errors:
                        log(f"⚠️ Дополнительные ошибки: {', '.join(additional_errors)}")
            except ValueError:
                log("❌ Ответ не содержит валидного JSON")
            
            results['feedback_api'] = {
                'status': 'OK' if response.status_code == 200 and not error else 'ERROR',
                'code': response.status_code,
                'response_time': f"{elapsed_time:.2f} сек"
            }
            
            if error:
                results['feedback_api']['error'] = response_data.get('errorText', 'Неизвестная ошибка')
                
        except requests.exceptions.Timeout:
            log("⏱ Тайм-аут при проверке API отзывов")
            results['feedback_api'] = {
                'status': 'ERROR',
                'error': "Тайм-аут запроса (превышено время ожидания)"
            }
        except requests.exceptions.ConnectionError:
            log("🌐 Ошибка соединения при проверке API отзывов")
            results['feedback_api'] = {
                'status': 'ERROR',
                'error': "Ошибка соединения с сервером"
            }
        except Exception as e:
            log(f"❌ Ошибка при проверке API отзывов: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            results['feedback_api'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        log("✅ Проверка API завершена")
        return results

class TelegramBot:
    def __init__(self, bot_token, chat_id, wb_api):
        log("🔧 Инициализация TelegramBot")
        self.bot_token = bot_token
        log(f"🔑 Токен бота: {bot_token[:10]}...")
        self.chat_ids = [id.strip() for id in chat_id.split(',')]
        log(f"👥 ID чатов: {self.chat_ids}")
        self.wb_api = wb_api
        
        log("🔄 Создание приложения Telegram...")
        self.app = Application.builder().token(bot_token).build()
        
        # Добавляем обработчик для всех сообщений (не только команд)
        log("📱 Настройка обработчика всех сообщений...")
        
        # Регистрация обработчиков команд
        log("📱 Регистрация обработчиков команд...")
        try:
            # Добавляем общий обработчик для всех текстовых сообщений
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            log("✅ Обработчик текстовых сообщений зарегистрирован")
            
            # Регистрируем обработчики команд
            self.app.add_handler(CommandHandler("status", self.status_command))
            log("✅ Команда /status зарегистрирована")
            self.app.add_handler(CommandHandler("start", self.start_command))
            log("✅ Команда /start зарегистрирована")
            self.app.add_handler(CommandHandler("help", self.help_command))
            log("✅ Команда /help зарегистрирована")
            self.app.add_handler(CommandHandler("test", self.test_command))
            log("✅ Команда /test зарегистрирована")
            
            # Добавляем обработчик для inline-кнопок
            self.app.add_handler(CallbackQueryHandler(self.button_handler))
            log("✅ Обработчик inline-кнопок зарегистрирован")
            
            # Добавляем обработчик ошибок
            self.app.add_error_handler(self.error_handler)
            log("✅ Обработчик ошибок зарегистрирован")
        except Exception as e:
            log(f"❌ Ошибка при регистрации команд: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
        
        log("✅ TelegramBot инициализирован")
    
    async def button_handler(self, update: Update, context: CallbackContext):
        """Обработчик нажатий на inline-кнопки"""
        query = update.callback_query
        await query.answer()  # Отвечаем на callback, чтобы убрать часы загрузки
        
        log(f"🔘 Нажата кнопка: {query.data} от пользователя {query.from_user.id}")
        
        # Проверяем права доступа
        if str(query.from_user.id) not in self.chat_ids:
            log(f"❌ Доступ запрещен для пользователя {query.from_user.id}")
            await query.message.reply_text("❌ У вас нет доступа к этой функции.")
            return
        
        # Обрабатываем разные типы кнопок
        if query.data == "status":
            # Вызываем проверку статуса
            log(f"🔄 Запуск команды status из кнопки для пользователя {query.from_user.id}")
            await self.status_callback(query)
        elif query.data == "help":
            # Показываем справку
            log(f"🔄 Запуск команды help из кнопки для пользователя {query.from_user.id}")
            await self.help_callback(query)
        elif query.data == "start":
            # Показываем главное меню
            log(f"🔄 Запуск команды start из кнопки для пользователя {query.from_user.id}")
            await self.start_callback(query)
        elif query.data == "check_now":
            # Выполняем внеплановую проверку
            log(f"🔄 Запуск внеплановой проверки для пользователя {query.from_user.id}")
            await self.check_now_callback(query)
        elif query.data == "test":
            # Показываем меню выбора тестовых уведомлений
            log(f"🔄 Показ меню тестовых уведомлений для пользователя {query.from_user.id}")
            await self.test_callback(query)
        elif query.data == "test_order":
            # Отправляем тестовый заказ и удаляем меню выбора
            log(f"🔄 Отправка тестового заказа для пользователя {query.from_user.id}")
            success = await self.send_test_notification("order")
            
            # Если успешно отправили, удаляем старые кнопки
            if success:
                try:
                    # Удаляем меню выбора, чтобы не было двойных кнопок
                    await query.message.edit_text(
                        "✅ <b>Тестовый заказ отправлен!</b>\n\n"
                        "Проверьте новое сообщение ниже ⬇️",
                        parse_mode='HTML'
                    )
                    log(f"✅ Меню выбора скрыто после отправки тестового заказа для пользователя {query.from_user.id}")
                except Exception as e:
                    log(f"⚠️ Не удалось удалить меню выбора: {e}")
            
        elif query.data == "test_sale":
            # Отправляем тестовый выкуп и удаляем меню выбора
            log(f"🔄 Отправка тестового выкупа для пользователя {query.from_user.id}")
            success = await self.send_test_notification("sale")
            
            # Если успешно отправили, удаляем старые кнопки
            if success:
                try:
                    # Удаляем меню выбора, чтобы не было двойных кнопок
                    await query.message.edit_text(
                        "✅ <b>Тестовый выкуп отправлен!</b>\n\n"
                        "Проверьте новое сообщение ниже ⬇️",
                        parse_mode='HTML'
                    )
                    log(f"✅ Меню выбора скрыто после отправки тестового выкупа для пользователя {query.from_user.id}")
                except Exception as e:
                    log(f"⚠️ Не удалось удалить меню выбора: {e}")
            
        elif query.data == "test_feedback":
            # Отправляем тестовое уведомление об отзыве и удаляем меню выбора
            log(f"🔄 Отправка тестового отзыва для пользователя {query.from_user.id}")
            success = await self.send_test_notification("feedback")
            
            # Если успешно отправили, удаляем старые кнопки
            if success:
                try:
                    # Удаляем меню выбора, чтобы не было двойных кнопок
                    await query.message.edit_text(
                        "✅ <b>Тестовый отзыв отправлен!</b>\n\n"
                        "Проверьте новое сообщение ниже ⬇️",
                        parse_mode='HTML'
                    )
                    log(f"✅ Меню выбора скрыто после отправки тестового отзыва для пользователя {query.from_user.id}")
                except Exception as e:
                    log(f"⚠️ Не удалось удалить меню выбора: {e}")
    
    async def start_callback(self, query):
        """Обработка нажатия на кнопку 'На главную'"""
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("📊 Статус API", callback_data="status"),
                InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
            ],
            [
                InlineKeyboardButton("❓ Помощь", callback_data="help"),
                InlineKeyboardButton("🧪 Тест", callback_data="test")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Обновляем текст сообщения
        await query.message.edit_text(
            "👋 <b>Бот для мониторинга Wildberries</b>\n\n"
            "📊 Я отслеживаю новые заказы, продажи и отзывы.\n"
            "🔄 Выберите одну из опций ниже:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        log(f"✅ Главное меню отправлено пользователю {query.from_user.id}")
    
    async def check_now_callback(self, query):
        """Обработчик внеплановой проверки"""
        try:
            # Сообщаем пользователю о начале проверки
            status_message = await query.message.edit_text(
                "🔍 Выполняю внеплановую проверку на наличие новых данных...",
                reply_markup=None  # Убираем кнопки на время проверки
            )
            
            log(f"🔍 Начало внеплановой проверки для пользователя {query.from_user.id}")
            
            # Выполняем проверки в отдельных задачах
            orders_task = asyncio.create_task(check_orders_async(self, self.wb_api))
            feedbacks_task = asyncio.create_task(check_feedbacks_async(self, self.wb_api))
            sales_task = asyncio.create_task(check_sales_async(self, self.wb_api))
            
            # Ждем завершения всех проверок
            await asyncio.gather(orders_task, feedbacks_task, sales_task)
            
            log(f"✅ Внеплановая проверка завершена для пользователя {query.from_user.id}")
            
            # Создаем клавиатуру для сообщения о результатах
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Проверить еще раз", callback_data="check_now"),
                    InlineKeyboardButton("🏠 На главную", callback_data="start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение о завершении проверки
            await status_message.edit_text(
                "✅ <b>Внеплановая проверка завершена!</b>\n\n"
                "Если были обнаружены новые заказы, выкупы или отзывы, "
                "вы получили соответствующие уведомления.\n\n"
                f"⏰ Время проверки: {get_moscow_time().strftime('%d.%m.%Y %H:%M:%S')}",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            log(f"❌ Ошибка при выполнении внеплановой проверки: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            
            # Создаем клавиатуру для сообщения об ошибке
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Повторить", callback_data="check_now"),
                    InlineKeyboardButton("🏠 На главную", callback_data="start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение об ошибке
            await query.message.edit_text(
                f"❌ <b>Ошибка при выполнении проверки</b>\n\n"
                f"Произошла ошибка: {str(e)}\n\n"
                "Пожалуйста, попробуйте позже или обратитесь к администратору.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
    
    async def status_callback(self, query):
        """Обработка нажатия на кнопку статуса"""
        try:
            # Изменяем текст сообщения на сообщение о проверке
            status_message = await query.message.edit_text(
                "🔍 Проверяю состояние API Wildberries...",
                reply_markup=None  # Убираем кнопки на время проверки
            )
            
            # Проверка статуса API
            log(f"🔄 Запуск проверки API для пользователя {query.from_user.id}")
            api_status = self.wb_api.check_api_status()
            log(f"📊 Результаты проверки API: {api_status}")
            
            # Формируем сообщение о статусе
            log("📝 Формирование сообщения о статусе")
            result_message = "📊 <b>Состояние API Wildberries</b>\n\n"
            
            # Статус API статистики
            stats_api = api_status.get('statistics_api', {})
            if stats_api.get('status') == 'OK':
                result_message += "✅ <b>API статистики:</b> Работает\n"
                result_message += f"⏱ Время ответа: {stats_api.get('response_time')}\n\n"
            else:
                result_message += "❌ <b>API статистики:</b> Ошибка\n"
                if 'error' in stats_api:
                    result_message += f"⚠️ Ошибка: {stats_api.get('error')}\n\n"
                else:
                    result_message += f"⚠️ Код ответа: {stats_api.get('code')}\n\n"
            
            # Статус API отзывов
            feedback_api = api_status.get('feedback_api', {})
            if feedback_api.get('status') == 'OK':
                result_message += "✅ <b>API отзывов:</b> Работает\n"
                result_message += f"⏱ Время ответа: {feedback_api.get('response_time')}\n\n"
            else:
                result_message += "❌ <b>API отзывов:</b> Ошибка\n"
                if 'error' in feedback_api:
                    result_message += f"⚠️ Ошибка: {feedback_api.get('error')}\n\n"
                else:
                    result_message += f"⚠️ Код ответа: {feedback_api.get('code')}\n\n"
            
            # Информация о боте
            result_message += "🤖 <b>Состояние бота</b>\n"
            result_message += f"⏰ Время проверки: {get_moscow_time().strftime('%d.%m.%Y %H:%M:%S')}\n"
            result_message += f"🔄 Интервал проверки данных: {CHECK_INTERVAL // 60} минут\n"
            
            # Создаем клавиатуру с кнопками
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Обновить статус", callback_data="status"),
                    InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
                ],
                [
                    InlineKeyboardButton("❓ Помощь", callback_data="help"),
                    InlineKeyboardButton("🏠 На главную", callback_data="start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            log(f"📤 Редактирование сообщения о статусе для пользователя {query.from_user.id}")
            log(f"📝 Содержимое: {result_message}")
            
            try:
                # Редактируем предыдущее сообщение вместо отправки нового
                await status_message.edit_text(
                    result_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                log(f"✅ Сообщение о статусе отредактировано для пользователя {query.from_user.id}")
            except Exception as edit_error:
                log(f"⚠️ Не удалось отредактировать сообщение: {edit_error}. Отправляем новое.")
                await query.message.reply_text(
                    result_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                log(f"✅ Отправлено новое сообщение о статусе пользователю {query.from_user.id}")
                
        except Exception as e:
            log(f"❌ Ошибка при обработке кнопки status: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            try:
                # Восстанавливаем кнопки в случае ошибки
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Обновить статус", callback_data="status"),
                        InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
                    ],
                    [
                        InlineKeyboardButton("❓ Помощь", callback_data="help"),
                        InlineKeyboardButton("🏠 На главную", callback_data="start")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.edit_text(
                    f"❌ Ошибка при получении статуса: {e}\nПопробуйте позже.",
                    reply_markup=reply_markup
                )
            except Exception as e2:
                log(f"❌ Ошибка при отправке сообщения об ошибке: {e2}")
    
    async def help_callback(self, query):
        """Обработка нажатия на кнопку помощи"""
        help_text = (
            "📖 <b>Справка по боту</b>\n\n"
            "Этот бот мониторит ваш аккаунт Wildberries и отправляет уведомления о:\n"
            "• 🛍 Новых заказах\n"
            "• 💰 Новых выкупах (продажах)\n"
            "• ⭐️ Новых отзывах и вопросах\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Запуск бота и показ кнопок\n"
            "/status - Проверка статуса API\n"
            "/test - Отправка тестовых уведомлений\n"
            "/help - Показ этой справки\n\n"
            "<b>Или используйте кнопки под сообщениями!</b>\n\n"
            "🔍 <b>Кнопка \"Проверить сейчас\"</b> позволяет выполнить внеплановую проверку "
            "на наличие новых заказов, выкупов и отзывов, не дожидаясь регулярной проверки."
        )
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("📊 Статус API", callback_data="status"),
                InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
            ],
            [
                InlineKeyboardButton("🏠 На главную", callback_data="start"),
                InlineKeyboardButton("🧪 Тест", callback_data="test")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Обновляем сообщение
        await query.message.edit_text(
            help_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        log(f"✅ Справка отправлена пользователю {query.from_user.id}")
    
    async def message_handler(self, update: Update, context: CallbackContext):
        """Обработчик всех текстовых сообщений"""
        if update.message:
            user_id = update.effective_user.id
            text = update.message.text
            log(f"📨 Получено сообщение от пользователя {user_id}: {text}")
            
            # Простой ответ на все сообщения, не являющиеся командами
            if str(user_id) in self.chat_ids:
                log(f"📤 Отправка ответа пользователю {user_id}")
                
                # Создаем клавиатуру с кнопками
                keyboard = [
                    [
                        InlineKeyboardButton("📊 Статус API", callback_data="status"),
                        InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "👋 Я понимаю только команды или кнопки.\nВыберите одну из доступных опций ниже:",
                    reply_markup=reply_markup
                )
                log(f"✅ Ответ с кнопками отправлен пользователю {user_id}")
    
    async def error_handler(self, update, context):
        """Обработчик ошибок для бота Telegram"""
        log(f"❌ Ошибка при обработке обновления: {context.error}")
        log(f"📋 Стек вызовов: {traceback.format_exc()}")
        log(f"🔍 Данные обновления: {update}")
    
    async def start_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        log(f"📥 Получена команда /start от пользователя {user_id}")
        
        # Проверяем права доступа
        if str(user_id) not in self.chat_ids:
            log(f"❌ Доступ запрещен для пользователя {user_id}")
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("📊 Статус API", callback_data="status"),
                InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
            ],
            [
                InlineKeyboardButton("❓ Помощь", callback_data="help"),
                InlineKeyboardButton("🧪 Тест", callback_data="test")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 <b>Привет! Я бот для мониторинга Wildberries.</b>\n\n"
            "📊 Я буду отправлять уведомления о новых заказах, продажах и отзывах.\n"
            "🔄 Используйте кнопки ниже для взаимодействия со мной:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        log(f"📤 Отправлен ответ на команду /start с кнопками пользователю {user_id}")
    
    async def help_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        log(f"📥 Получена команда /help от пользователя {user_id}")
        
        # Проверяем права доступа
        if str(user_id) not in self.chat_ids:
            log(f"❌ Доступ запрещен для пользователя {user_id}")
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        
        help_text = (
            "📖 <b>Справка по боту</b>\n\n"
            "Этот бот мониторит ваш аккаунт Wildberries и отправляет уведомления о:\n"
            "• 🛍 Новых заказах\n"
            "• 💰 Новых выкупах (продажах)\n"
            "• ⭐️ Новых отзывах и вопросах\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Запуск бота и показ кнопок\n"
            "/status - Проверка статуса API\n"
            "/test - Отправка тестовых уведомлений\n"
            "/help - Показ этой справки\n\n"
            "<b>Или используйте кнопки под сообщениями!</b>\n\n"
            "🔍 <b>Кнопка \"Проверить сейчас\"</b> позволяет выполнить внеплановую проверку "
            "на наличие новых заказов, выкупов и отзывов, не дожидаясь регулярной проверки."
        )
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("📊 Статус API", callback_data="status"),
                InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
            ],
            [
                InlineKeyboardButton("🏠 На главную", callback_data="start"),
                InlineKeyboardButton("🧪 Тест", callback_data="test")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        log(f"📤 Отправлен ответ на команду /help с кнопками пользователю {user_id}")
        
    async def status_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /status - проверка работы бота и API"""
        try:
            log("🔄 Начало обработки команды /status")
            user_id = update.effective_user.id
            log(f"👤 ID пользователя: {user_id}")
            
            # Проверяем, имеет ли пользователь право на выполнение команды
            log(f"🔒 Проверка прав доступа для пользователя {user_id}")
            log(f"👥 Разрешенные ID: {self.chat_ids}")
            has_access = str(user_id) in self.chat_ids
            log(f"✅ Имеет доступ: {has_access}")
            
            if not has_access:
                log(f"❌ Доступ запрещен для пользователя {user_id}")
                await update.message.reply_text("❌ У вас нет доступа к этой команде.")
                return
            
            log(f"🔄 Отправка сообщения о начале проверки для пользователя {user_id}")
            status_message = await update.message.reply_text("🔍 Проверяю состояние API Wildberries...")
            
            # Проверка статуса API
            log(f"🔄 Запуск проверки API для пользователя {user_id}")
            api_status = self.wb_api.check_api_status()
            log(f"📊 Результаты проверки API: {api_status}")
            
            # Формируем сообщение о статусе
            log("📝 Формирование сообщения о статусе")
            result_message = "📊 <b>Состояние API Wildberries</b>\n\n"
            
            # Статус API статистики
            stats_api = api_status.get('statistics_api', {})
            if stats_api.get('status') == 'OK':
                result_message += "✅ <b>API статистики:</b> Работает\n"
                result_message += f"⏱ Время ответа: {stats_api.get('response_time')}\n\n"
            else:
                result_message += "❌ <b>API статистики:</b> Ошибка\n"
                if 'error' in stats_api:
                    result_message += f"⚠️ Ошибка: {stats_api.get('error')}\n\n"
                else:
                    result_message += f"⚠️ Код ответа: {stats_api.get('code')}\n\n"
            
            # Статус API отзывов
            feedback_api = api_status.get('feedback_api', {})
            if feedback_api.get('status') == 'OK':
                result_message += "✅ <b>API отзывов:</b> Работает\n"
                result_message += f"⏱ Время ответа: {feedback_api.get('response_time')}\n\n"
            else:
                result_message += "❌ <b>API отзывов:</b> Ошибка\n"
                if 'error' in feedback_api:
                    result_message += f"⚠️ Ошибка: {feedback_api.get('error')}\n\n"
                else:
                    result_message += f"⚠️ Код ответа: {feedback_api.get('code')}\n\n"
            
            # Информация о боте
            result_message += "🤖 <b>Состояние бота</b>\n"
            result_message += f"⏰ Время проверки: {get_moscow_time().strftime('%d.%m.%Y %H:%M:%S')}\n"
            result_message += f"🔄 Интервал проверки данных: {CHECK_INTERVAL // 60} минут\n"
            
            # Создаем клавиатуру с кнопками
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Обновить статус", callback_data="status"),
                    InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
                ],
                [
                    InlineKeyboardButton("❓ Помощь", callback_data="help"),
                    InlineKeyboardButton("🏠 На главную", callback_data="start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            log(f"📤 Редактирование сообщения о статусе для пользователя {user_id}")
            log(f"📝 Содержимое: {result_message}")
            
            try:
                # Редактируем предыдущее сообщение вместо отправки нового
                await status_message.edit_text(
                    result_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                log(f"✅ Сообщение о статусе отредактировано для пользователя {user_id}")
            except Exception as edit_error:
                log(f"⚠️ Не удалось отредактировать сообщение: {edit_error}. Отправляем новое.")
                await update.message.reply_text(
                    result_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                log(f"✅ Отправлено новое сообщение о статусе пользователю {user_id}")
                
        except Exception as e:
            log(f"❌ Ошибка при обработке команды /status: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            try:
                error_message = f"❌ Произошла ошибка при выполнении команды:\n{str(e)}\n\nПопробуйте позже или свяжитесь с администратором."
                
                # Создаем клавиатуру с кнопкой для повторной попытки
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Повторить", callback_data="status"),
                        InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.message:
                    await update.message.reply_text(
                        error_message,
                        reply_markup=reply_markup
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_text(
                        error_message,
                        reply_markup=reply_markup
                    )
            except Exception as e2:
                log(f"❌ Ошибка при отправке сообщения об ошибке: {e2}")
    
    async def test_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /test для отправки тестовых уведомлений"""
        user_id = update.effective_user.id
        log(f"📥 Получена команда /test от пользователя {user_id}")
        
        # Проверяем права доступа
        if str(user_id) not in self.chat_ids:
            log(f"❌ Доступ запрещен для пользователя {user_id}")
            await update.message.reply_text("❌ У вас нет доступа к этой команде.")
            return
        
        # Создаем клавиатуру с кнопками для выбора типа тестового уведомления
        keyboard = [
            [
                InlineKeyboardButton("🛍 Заказ", callback_data="test_order"),
                InlineKeyboardButton("💰 Выкуп", callback_data="test_sale")
            ],
            [
                InlineKeyboardButton("⭐️ Отзыв", callback_data="test_feedback"),
                InlineKeyboardButton("🏠 На главную", callback_data="start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🧪 <b>Тестовые уведомления</b>\n\n"
            "Выберите тип уведомления, которое вы хотите отправить в тестовом режиме:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        log(f"📤 Отправлен ответ на команду /test с кнопками пользователю {user_id}")
    
    async def send_test_notification(self, notification_type):
        """Отправка тестового уведомления выбранного типа"""
        log(f"🧪 Отправка тестового уведомления типа: {notification_type}")
        
        if notification_type == "order":
            # Тестовый заказ
            test_order = {
                "date": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "supplierArticle": "TEST-ARTICLE-123",
                "finishedPrice": "1500.00",
                "priceWithDisc": "1275.00",
                "totalPrice": "1350.00",
                "regionName": "Москва",
                "oblastOkrugName": "Центральный округ",
                "warehouseName": "Коледино",
                "warehouseType": "Dropoff/Доставка"
            }
            message = format_order_message(test_order)
            
        elif notification_type == "sale":
            # Тестовый выкуп
            test_sale = {
                "date": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "supplierArticle": "TEST-ARTICLE-456",
                "brand": "TestBrand",
                "subject": "Тестовый товар",
                "forPay": "2000.00",
                "feeWB": "200.00",
                "finishedPrice": "1800.00",
                "regionName": "Санкт-Петербург"
            }
            message = format_sale_message(test_sale)
            
        elif notification_type == "feedback":
            # Тестовый отзыв
            feedback_data = {
                "has_new_feedbacks": True,
                "has_new_questions": True,
                "feedbacks_count": 2,
                "questions_count": 1
            }
            message = (
                "❗️ <b>Пришел новый отзыв или вопрос!</b>\n\n"
                "Проверьте портал продавца.\n\n"
                "<i>Это тестовое уведомление.</i>"
            )
        else:
            log(f"❌ Неизвестный тип уведомления: {notification_type}")
            return
        
        # Добавляем пометку о тестовом характере уведомления
        if notification_type != "feedback":  # Для feedback уже добавили
            message += "\n\n<i>Это тестовое уведомление.</i>"
        
        # Отправляем уведомление в чат
        for chat_id in self.chat_ids:
            try:
                log(f"📤 Отправка тестового уведомления типа {notification_type} в чат {chat_id}")
                # Добавляем кнопки навигации к тестовому уведомлению
                keyboard = [
                    [
                        InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now"),
                        InlineKeyboardButton("🏠 На главную", callback_data="start")
                    ],
                    [
                        InlineKeyboardButton("🧪 Еще тесты", callback_data="test"),
                        InlineKeyboardButton("❓ Помощь", callback_data="help")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Отправляем сообщение с кнопками навигации
                await self.app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                log(f"✅ Тестовое уведомление с кнопками отправлено в чат {chat_id}")
            except Exception as e:
                log(f"❌ Ошибка при отправке тестового уведомления в чат {chat_id}: {e}")
                log(f"📋 Стек вызовов: {traceback.format_exc()}")
        
        log(f"✅ Тестовое уведомление типа {notification_type} успешно отправлено")
        return True
    
    async def send_notification(self, message):
        """Отправка уведомления в Telegram"""
        log("📤 Отправка уведомления")
        try:
            for chat_id in self.chat_ids:
                log(f"📤 Отправка уведомления в чат {chat_id}")
                await self.app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='HTML'
                )
                log(f"✅ Уведомление отправлено в чат {chat_id}")
                await asyncio.sleep(0.1)  # Небольшая задержка между отправками
        except Exception as e:
            log(f"❌ Ошибка при отправке уведомления: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
    
    async def start_bot(self):
        """Запуск бота Telegram"""
        log("🚀 Запуск бота Telegram")
        try:
            log("🔄 Инициализация приложения")
            await self.app.initialize()
            log("✅ Приложение инициализировано")
            
            log("🔄 Запуск приложения")
            await self.app.start()
            log("✅ Приложение запущено")
            
            log("🔄 Запуск получения обновлений")
            log(f"🔄 Настройки updater: {self.app.updater}")
            
            # Логирование URL для обновлений
            if hasattr(self.app.updater, 'url'):
                log(f"🔄 URL для обновлений: {self.app.updater.url}")
            
            # Улучшенные настройки для получения обновлений
            log("🔄 Настройка параметров для получения обновлений")
            log("📋 Допустимые типы обновлений: message, edited_message, channel_post, edited_channel_post, message_reaction, message_reaction_count, callback_query")
            log("⚙️ Таймаут чтения: 30 сек, таймаут подключения: 10 сек")
            log("⚙️ Пропуск ожидающих обновлений: Нет")
            
            await self.app.updater.start_polling(
                drop_pending_updates=False,
                allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post", "message_reaction", "message_reaction_count", "callback_query"],
                read_timeout=30,
                connect_timeout=10
            )
            log("✅ Получение обновлений запущено")
            
            # Дополнительное уведомление о готовности бота
            for chat_id in self.chat_ids:
                try:
                    log(f"📢 Отправка тестового сообщения в чат {chat_id}")
                    
                    # Создаем клавиатуру с кнопками для приветственного сообщения
                    keyboard = [
                        [
                            InlineKeyboardButton("📊 Статус API", callback_data="status"),
                            InlineKeyboardButton("🔍 Проверить сейчас", callback_data="check_now")
                        ],
                        [
                            InlineKeyboardButton("❓ Помощь", callback_data="help"),
                            InlineKeyboardButton("🧪 Тест", callback_data="test")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await self.app.bot.send_message(
                        chat_id=chat_id,
                        text="🤖 <b>Бот запущен и готов к работе!</b>\n\nВыберите действие ниже:",
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                    log(f"✅ Тестовое сообщение с кнопками отправлено в чат {chat_id}")
                except Exception as e:
                    log(f"❌ Ошибка при отправке тестового сообщения в чат {chat_id}: {e}")
                    log(f"📋 Стек вызовов: {traceback.format_exc()}")
            
            log("✅ Бот запущен и готов принимать команды")
        except Exception as e:
            log(f"❌ Ошибка при запуске бота: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            raise

    async def test_callback(self, query):
        """Обработка нажатия на кнопку тестовых уведомлений"""
        log(f"🧪 Подготовка меню тестовых уведомлений для пользователя {query.from_user.id}")
        
        # Создаем клавиатуру с кнопками для выбора типа тестового уведомления
        keyboard = [
            [
                InlineKeyboardButton("🛍 Заказ", callback_data="test_order"),
                InlineKeyboardButton("💰 Выкуп", callback_data="test_sale")
            ],
            [
                InlineKeyboardButton("⭐️ Отзыв", callback_data="test_feedback"),
                InlineKeyboardButton("🏠 На главную", callback_data="start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Обновляем текст сообщения
        await query.message.edit_text(
            "🧪 <b>Тестовые уведомления</b>\n\n"
            "Выберите тип уведомления, которое вы хотите отправить в тестовом режиме:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        log(f"✅ Меню тестовых уведомлений отправлено пользователю {query.from_user.id}")

def format_order_message(order):
    """Форматирование сообщения о новом заказе (товар заказан, но еще не получен)"""
    # Парсим дату
    try:
        # Используем вспомогательную функцию для парсинга даты
        order_date = parse_date_string(order['date'])
    except Exception as e:
        log(f"❌ Ошибка при парсинге даты заказа: {e}")
        order_date = datetime.now()
    
    return (
        f"🛍 <b>Новый заказ!</b>\n\n"
        f"📝 Артикул: {order.get('supplierArticle')}\n"
        f"💳 Заплатил покупатель: {order.get('finishedPrice')} ₽\n"
        f"💵 Цена продажи: {order.get('priceWithDisc')} ₽\n"
        f"📍 Регион: {order.get('regionName')} обл., {order.get('oblastOkrugName')}\n"
        f"🏪 Склад: {order.get('warehouseName')} ({order.get('warehouseType')})\n"
        f"📅 Дата: {order_date.strftime('%d.%m.%Y %H:%M')}"
    )

def format_sale_message(sale):
    """Форматирование сообщения о выкупе (товар получен и принят покупателем)"""
    # Парсим дату
    try:
        # Выбираем поле date или lastChangeDate, если date отсутствует
        date_string = sale.get('date', sale.get('lastChangeDate'))
        sale_date = parse_date_string(date_string)
    except Exception as e:
        log(f"❌ Ошибка при парсинге даты продажи: {e}")
        sale_date = datetime.now()
    
    return (
        f"💰 <b>Новый выкуп!</b>\n\n"
        f"📝 Артикул: {sale.get('supplierArticle')}\n"
        f"💵 Цена продажи: {sale.get('finishedPrice', 0)} ₽\n"
        f"🧮 Комиссия: {sale.get('feeWB', 0)} ₽\n"
        f"💸 К выплате: {sale.get('forPay', 0)} ₽\n"
        f"📍 Регион: {sale.get('regionName', 'Не указан')}\n"
        f"📅 Дата: {sale_date.strftime('%d.%m.%Y %H:%M')}"
    )

def parse_date_string(date_str):
    """Парсинг даты из API с поддержкой разных форматов"""
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # С миллисекундами
        '%Y-%m-%dT%H:%M:%S',      # Без миллисекунд
        '%Y-%m-%dT%H:%M:%SZ'      # С Z, но без миллисекунд
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    # Если ни один формат не подошел, логируем ошибку и возвращаем текущее время
    log(f"⚠️ Неподдерживаемый формат даты: {date_str}. Используем текущее время.")
    return datetime.now()

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения работы"""
    print("\n⛔️ Получен сигнал завершения. Останавливаем работу...")
    print("🔴 Мониторинг остановлен")
    sys.exit(0)

def main():
    """Основная функция приложения"""
    log("🚀 Запуск основной функции")
    try:
        # Регистрируем обработчик сигналов
        log("🔄 Регистрация обработчиков сигналов")
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        log("✅ Обработчики сигналов зарегистрированы")
        
        log("📢 Запуск мониторинга заказов и отзывов Wildberries...")
        log(f"⏰ Интервал проверки данных: каждые {CHECK_INTERVAL // 60} минут")
        
        # Инициализируем асинхронный бот и запускаем его
        try:
            # Создаем новый event loop вместо получения текущего
            log("🔄 Создание и настройка event loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            log("✅ Event loop создан и настроен")
            
            # Запускаем асинхронную основную функцию
            loop.run_until_complete(run_bot())
            
        except Exception as e:
            log(f"❌ Ошибка при запуске бота: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
            sys.exit(1)
        finally:
            # Закрываем event loop
            loop.close()
            log("✅ Event loop закрыт")
            log("🔴 Мониторинг остановлен")
            
    except Exception as e:
        log(f"❌ Критическая ошибка в main: {e}")
        log(f"📋 Стек вызовов: {traceback.format_exc()}")
        sys.exit(1)

async def run_bot():
    """Единая точка входа для асинхронной работы бота"""
    log("🚀 Запуск асинхронной работы бота")
    
    try:
        # Инициализация API и бота
        log("🔄 Инициализация WildberriesAPI")
        wb_api = WildberriesAPI(WB_API_TOKEN, WB_FEEDBACK_TOKEN)
        log("✅ WildberriesAPI инициализирован")
        
        log("🔄 Инициализация TelegramBot")
        telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, wb_api)
        log("✅ TelegramBot инициализирован")
        
        # Отправляем уведомление о запуске
        log("🔄 Отправка уведомления о запуске")
        try:
            await telegram_bot.send_notification(
                "🟢 <b>Мониторинг запущен</b>\n\n"
                f"⏱ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                f"🔄 Интервал проверки данных: {CHECK_INTERVAL // 60} минут\n"
                "ℹ️ Данные будут проверяться автоматически и вы получите уведомление только о новых событиях.\n"
                "📱 Используйте команду /status для проверки работы бота и API.\n"
                "🧪 Используйте команду /test для отправки тестовых уведомлений."
            )
            log("✅ Уведомление о запуске отправлено")
        except Exception as e:
            log(f"❌ Ошибка при отправке уведомления о запуске: {e}")
            log(f"📋 Стек вызовов: {traceback.format_exc()}")
        
        # Проверяем токен бота
        log(f"🔑 Проверка токена бота: {TELEGRAM_BOT_TOKEN[:10]}...")
        log(f"👥 Чат ID для уведомлений: {TELEGRAM_CHAT_ID}")
        
        # Запускаем бота
        log("🔄 Запуск бота")
        await telegram_bot.start_bot()
        log("✅ Бот успешно стартовал и ожидает команд")
        
        log("🔄 Запуск задачи периодических проверок")
        # Запускаем основной цикл проверок
        await run_periodic_checks(telegram_bot, wb_api)
    
    except asyncio.CancelledError:
        log("🛑 Задача была отменена")
    except Exception as e:
        log(f"❌ Ошибка в run_bot: {e}")
        log(f"📋 Стек вызовов: {traceback.format_exc()}")
        raise

async def run_periodic_checks(telegram_bot, wb_api):
    """Запуск периодических проверок в асинхронном режиме"""
    log("🔄 Запуск периодических проверок")
    
    try:
        while True:
            log(f"🔍 Запуск проверок ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            
            # Проверяем новые заказы
            try:
                log("🔍 Проверка новых заказов")
                await check_orders_async(telegram_bot, wb_api)
            except Exception as e:
                log(f"❌ Ошибка при проверке заказов: {e}")
                log(f"📋 Стек вызовов: {traceback.format_exc()}")
            
            # Проверяем отзывы
            try:
                log("👀 Проверка отзывов")
                await check_feedbacks_async(telegram_bot, wb_api)
            except Exception as e:
                log(f"❌ Ошибка при проверке отзывов: {e}")
                log(f"📋 Стек вызовов: {traceback.format_exc()}")
            
            # Проверяем продажи
            try:
                log("💰 Проверка продаж")
                await check_sales_async(telegram_bot, wb_api)
            except Exception as e:
                log(f"❌ Ошибка при проверке продаж: {e}")
                log(f"📋 Стек вызовов: {traceback.format_exc()}")
            
            log(f"✅ Проверки завершены, следующий запуск через {CHECK_INTERVAL} секунд")
            # Ждем до следующего интервала проверки
            await asyncio.sleep(CHECK_INTERVAL)
            
    except asyncio.CancelledError:
        log("🛑 Периодические проверки остановлены")
    except Exception as e:
        log(f"❌ Ошибка в run_periodic_checks: {e}")
        log(f"📋 Стек вызовов: {traceback.format_exc()}")
        raise

# Асинхронные версии функций проверки
async def check_orders_async(telegram_bot, wb_api):
    """Проверка новых заказов и отправка уведомлений"""
    log(f"🔍 Проверка новых заказов ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})...")
    
    new_orders = wb_api.get_new_orders()
    if new_orders:
        log(f"📬 Найдено {len(new_orders)} новых заказов")
        for order in new_orders:
            message = format_order_message(order)
            await telegram_bot.send_notification(message)
            await asyncio.sleep(0.5)
    else:
        log("📭 Новых заказов нет")

async def check_feedbacks_async(telegram_bot, wb_api):
    """Проверка новых отзывов и вопросов"""
    log(f"👀 Проверка отзывов и вопросов ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})...")
    
    feedback_data = wb_api.check_new_feedbacks()
    if feedback_data is not None:
        has_new = feedback_data['has_new_feedbacks'] or feedback_data['has_new_questions']
        if has_new:
            message = (
                "❗️ <b>Пришел новый отзыв или вопрос!</b>\n\n"
                "Проверьте портал продавца."
            )
            await telegram_bot.send_notification(message)
            log(f"📢 Обнаружено: {feedback_data['feedbacks_count']} отзывов, {feedback_data['questions_count']} вопросов")

async def check_sales_async(telegram_bot, wb_api):
    """Проверка новых выкупов"""
    log(f"💰 Проверка выкупов ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})...")
    
    sales = wb_api.get_sales()
    
    if sales:
        log(f"📈 Найдено {len(sales)} новых выкупов")
        for sale in sales:
            message = format_sale_message(sale)
            await telegram_bot.send_notification(message)
            await asyncio.sleep(0.5)
    else:
        log("📉 Новых выкупов нет")

if __name__ == "__main__":
    main() 
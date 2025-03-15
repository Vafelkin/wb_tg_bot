import requests
import schedule
import time
import signal
import sys
from datetime import datetime, timedelta
from telegram.ext import Application
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WB_API_TOKEN,
    WB_API_BASE_URL,
    CHECK_INTERVAL,
    FEEDBACK_CHECK_INTERVAL,
    ORDERS_DAYS_LOOK_BACK,
    MAX_ORDERS_PER_REQUEST,
    PAGINATION_DELAY
)

class WildberriesAPI:
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': token}
        self._last_order_time = datetime.now() - timedelta(days=ORDERS_DAYS_LOOK_BACK)
        self._processed_orders = set()  # Множество для хранения обработанных srid
        self._last_feedback_check = None
    
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
        raise ValueError(f"Неподдерживаемый формат даты: {date_str}")
    
    def get_new_orders(self):
        """Получение новых заказов с Wildberries с поддержкой пагинации"""
        all_orders = []
        next_date_from = self._last_order_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        while True:
            try:
                url = f"{WB_API_BASE_URL}/api/v1/supplier/orders"
                response = requests.get(
                    url,
                    headers={'Authorization': f'Bearer {self.token}'},
                    params={
                        'dateFrom': next_date_from,
                        'flag': 0  # 0 - новые заказы
                    }
                )
                response.raise_for_status()
                orders = response.json()
                
                # Если нет заказов, прерываем цикл
                if not orders:
                    break
                    
                # Добавляем только необработанные заказы
                new_orders = [
                    order for order in orders 
                    if order.get('srid') not in self._processed_orders
                ]
                all_orders.extend(new_orders)
                
                # Обновляем множество обработанных заказов
                self._processed_orders.update(order.get('srid') for order in new_orders)
                
                # Если получили меньше максимального количества, значит это последняя страница
                if len(orders) < MAX_ORDERS_PER_REQUEST:
                    break
                    
                # Берем дату последнего заказа для следующего запроса
                next_date_from = orders[-1]['lastChangeDate']
                
                # Добавляем задержку между запросами
                time.sleep(PAGINATION_DELAY)
                
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при получении заказов: {e}")
                break
        
        # Обновляем время последнего проверенного заказа
        if all_orders:
            self._last_order_time = max(
                self._parse_date(order['date'])
                for order in all_orders
            )
        
        return all_orders

    def check_new_feedbacks(self):
        """Проверка наличия новых отзывов и вопросов"""
        # Проверяем, прошла ли минута с последней проверки
        current_time = datetime.now()
        if self._last_feedback_check and (current_time - self._last_feedback_check).total_seconds() < 60:
            return None  # Возвращаем None, если прошло меньше минуты

        try:
            url = "https://feedbacks-api.wildberries.ru/api/v1/new-feedbacks-questions"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            self._last_feedback_check = current_time

            # Проверяем наличие ошибок
            if result.get('error'):
                print(f"Ошибка при проверке отзывов: {result.get('errorText')}")
                if result.get('additionalErrors'):
                    print(f"Дополнительные ошибки: {', '.join(result['additionalErrors'])}")
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
            
            return feedback_info

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при проверке отзывов и вопросов: {e}")
            return None

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_ids = [id.strip() for id in chat_id.split(',')]
        self.app = Application.builder().token(bot_token).build()
    
    async def send_notification(self, message):
        """Отправка уведомления в Telegram"""
        try:
            for chat_id in self.chat_ids:
                await self.app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='HTML'
                )
                await asyncio.sleep(0.1)  # Небольшая задержка между отправками
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")

def format_order_message(order):
    """Форматирование сообщения о заказе"""
    wb_api = WildberriesAPI(WB_API_TOKEN)
    order_date = wb_api._parse_date(order['date'])
    return (
        f"🛍 <b>Новый заказ!</b>\n\n"
        f"📝 Артикул продавца: {order.get('supplierArticle')}\n"
        f"💳 Заплатил покупатель: {order.get('finishedPrice')} ₽\n"
        f"💵 Вы получите: {order.get('priceWithDisc')} ₽\n"
        f"💰 Цена со скидкой: {order.get('totalPrice')} ₽\n"
        f"📍 Регион: {order.get('regionName')} обл., {order.get('oblastOkrugName')}\n"
        f"🏪 Склад: {order.get('warehouseName')} ({order.get('warehouseType')})\n"
        f"📅 Дата: {order_date.strftime('%d.%m.%Y %H:%M')}"
    )

async def send_status_notification(message):
    """Отправка уведомления о статусе работы скрипта"""
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    await notifier.send_notification(message)

async def check_orders():
    """Проверка новых заказов и отправка уведомлений"""
    wb_api = WildberriesAPI(WB_API_TOKEN)
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    print(f"🔍 Проверка новых заказов ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})...")
    
    new_orders = wb_api.get_new_orders()
    if new_orders:
        print(f"📬 Найдено {len(new_orders)} новых заказов")
        for order in new_orders:
            message = format_order_message(order)
            await notifier.send_notification(message)
            await asyncio.sleep(0.5)
    else:
        print("📭 Новых заказов нет")

async def check_feedbacks():
    """Проверка новых отзывов и вопросов"""
    wb_api = WildberriesAPI(WB_API_TOKEN)
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    print(f"👀 Проверка отзывов и вопросов ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})...")
    
    feedback_data = wb_api.check_new_feedbacks()
    if feedback_data is not None:
        has_new = feedback_data['has_new_feedbacks'] or feedback_data['has_new_questions']
        if has_new:
            message = (
                "❗️ <b>Новые отзывы или вопросы!</b>\n\n"
                f"📝 Новых отзывов: {feedback_data['feedbacks_count']}\n"
                f"❓ Новых вопросов: {feedback_data['questions_count']}\n\n"
                "Пожалуйста, проверьте личный кабинет WB."
            )
            await notifier.send_notification(message)
            print(f"📢 Обнаружено: {feedback_data['feedbacks_count']} отзывов, {feedback_data['questions_count']} вопросов")

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения работы"""
    print("\n⛔️ Получен сигнал завершения. Останавливаем работу...")
    # Отправляем уведомление об остановке
    asyncio.run(send_status_notification(
        "🔴 <b>Мониторинг заказов остановлен</b>\n\n"
        f"⏱ Время остановки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    ))
    sys.exit(0)

def main():
    """Основная функция приложения"""
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Запуск мониторинга заказов и отзывов Wildberries...")
    print(f"⏰ Интервал проверки заказов: {CHECK_INTERVAL} секунд")
    print(f"⏰ Интервал проверки отзывов: {FEEDBACK_CHECK_INTERVAL} секунд")
    
    # Отправляем уведомление о запуске
    asyncio.run(send_status_notification(
        "🟢 <b>Мониторинг запущен</b>\n\n"
        f"⏱ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"🔄 Интервал проверки заказов: {CHECK_INTERVAL // 60} минут\n"
        f"🔄 Интервал проверки отзывов: {FEEDBACK_CHECK_INTERVAL} секунд"
    ))
    
    # Выполняем первую проверку сразу при запуске
    asyncio.run(check_orders())
    asyncio.run(check_feedbacks())
    
    # Планируем регулярные проверки
    schedule.every(CHECK_INTERVAL).seconds.do(lambda: asyncio.run(check_orders()))
    schedule.every(FEEDBACK_CHECK_INTERVAL).seconds.do(lambda: asyncio.run(check_feedbacks()))
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    import asyncio
    main() 
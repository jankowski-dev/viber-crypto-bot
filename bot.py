from flask import Flask, request, jsonify
import requests
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
PORT = os.environ.get('PORT', 5000)

# ⚠️ ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ USER_ID
AUTHORIZED_USER_IDS = [
    'zV/BRbzyPWJHKFpMTLWkqw=='  # ← ЗАМЕНИТЕ ЭТО на ваш реальный ID
]

# Глобальная переменная для хранения последнего курса
current_btc_price = None

print("🤖 Private Viber Bot starting...")
print(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")

# Notion конфигурация (переменные окружения GitHub)
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

def get_notion_profits():
    """Получает данные из колонки 'Текущая прибыль' из Notion БД"""
    # Проверяем наличие токена и ID базы
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("❌ Notion credentials не настроены")
        return None

    try:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={})
        
        if response.status_code == 200:
            data = response.json()
            profits = []
            
            for page in data.get("results", []):
                # Получаем свойства страницы
                properties = page.get("properties", {})
                
                # Ищем колонку "Текущая прибыль"
                if "Текущая прибыль" in properties:
                    profit_property = properties["Текущая прибыль"]
                    
                    # Извлекаем значение в зависимости от типа
                    if profit_property.get("type") == "number":
                        profit_value = profit_property.get("number")
                        if profit_value is not None:
                            profits.append(f"${profit_value:,.2f}")
                    elif profit_property.get("type") == "formula":
                        formula_result = profit_property.get("formula", {}).get("number")
                        if formula_result is not None:
                            profits.append(f"${formula_result:,.2f}")
            
            return profits
        else:
            print(f"❌ Notion API error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting Notion data: {e}")
        return None

def get_notion_test_message():
    """Получает и форматирует данные из Notion для отображения"""
    profits = get_notion_profits()
    
    if profits is None:
        return """🧪 Тест Notion

❌ Не удалось получить данные из Notion

Возможные причины:
• Неверный токен API
• Неверный ID базы данных
• Нет доступа к базе данных
• Колонка "Текущая прибыль" не найдена

Проверьте настройки подключения к Notion."""
    
    if not profits:
        return """🧪 Тест Notion

⚠️ Подключение к Notion успешно, но данные не найдены

Возможные причины:
• База данных пуста
• Колонка "Текущая прибыль" пуста
• Неверное название колонки

Проверьте структуру базы данных."""
    
    # Форматируем данные для отображения
    message = "🧪 Тест Notion\n\n📊 Данные из колонки 'Текущая прибыль':\n\n"
    
    for i, profit in enumerate(profits, 1):
        message += f"• Запись {i}: {profit}\n"
    
    message += f"\n✅ Найдено записей: {len(profits)}"
    
    return message

def get_btc_price():
    """Получает текущий курс биткоина с CoinGecko"""
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            btc_price = data['bitcoin']['usd']
            change_24h = data['bitcoin']['usd_24h_change']
            return {
                'price': float(btc_price),
                'change_24h': float(change_24h)
            }
        else:
            print(f"❌ CoinGecko API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting BTC price from CoinGecko: {e}")
        return None

def send_btc_updates():
    """Отправляет обновления курса BTC всем авторизованным пользователям"""
    global current_btc_price
    
    print(f"🔄 Sending BTC update at {datetime.now().strftime('%H:%M:%S')}")
    
    btc_data = get_btc_price()
    if btc_data is not None:
        price = btc_data['price']
        change_24h = btc_data['change_24h']
        current_btc_price = price
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Форматируем изменение за 24 часа
        if change_24h > 0:
            change_emoji = "📈"
            change_text = f"+{change_24h:.2f}%"
        else:
            change_emoji = "📉"
            change_text = f"{change_24h:.2f}%"
        
        message = f"""📊 Bitcoin (BTC)

💰 ${price:,.2f}
{change_emoji} 24ч: {change_text}

🕒 {timestamp}
⏰ Обновляется каждые 30 секунд"""
        
        success_count = 0
        # Отправляем всем авторизованным пользователям
        for user_id in AUTHORIZED_USER_IDS:
            if send_message(user_id, message, create_main_menu()):
                success_count += 1
                print(f"📤 Sent BTC price to {user_id[:8]}...")
            else:
                print(f"❌ Failed to send to {user_id[:8]}...")
        
        print(f"✅ BTC update completed: {success_count}/{len(AUTHORIZED_USER_IDS)} users")
        print(f"💰 Current price: ${price:,.2f} | Change: {change_24h:.2f}%")
    else:
        print("❌ Failed to get BTC price from CoinGecko")

def btc_scheduler():
    """Фоновая задача для отправки курса BTC каждые 30 секунд"""
    while True:
        try:
            send_btc_updates()
            time.sleep(30)  # Каждые 30 секунд
        except Exception as e:
            print(f"❌ Error in BTC scheduler: {e}")
            time.sleep(30)  # При ошибке тоже ждем 30 секунд

def create_main_menu():
    """Создает главное меню с категориями"""
    return {
        "Type": "keyboard",
        "DefaultHeight": False,
        "Buttons": [
            {
                "ActionType": "reply",
                "ActionBody": "menu_crypto",
                "Text": "₿ Крипто",
                "TextSize": "large",
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply", 
                "ActionBody": "menu_info",
                "Text": "ℹ️ Инфо",
                "TextSize": "large", 
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply",
                "ActionBody": "test_notion",
                "Text": "🧪 Тест Notion",
                "TextSize": "large",
                "Columns": 2,
                "Rows": 1
            }
        ],
        "ButtonSize": "large"
    }

def create_crypto_menu():
    """Создает меню криптовалют"""
    return {
        "Type": "keyboard",
        "DefaultHeight": False,
        "Buttons": [
            {
                "ActionType": "reply",
                "ActionBody": "crypto_view",
                "Text": "👁️ Просмотр",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply",
                "ActionBody": "crypto_months",
                "Text": "📆 По месяцам",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply",
                "ActionBody": "back_to_main",
                "Text": "⬅️ Назад",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            }
        ],
        "ButtonSize": "regular"
    }

def create_info_menu():
    """Создает меню информации"""
    return {
        "Type": "keyboard",
        "DefaultHeight": False,
        "Buttons": [
            {
                "ActionType": "reply",
                "ActionBody": "info_schedule",
                "Text": "⏰ Расписание",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply",
                "ActionBody": "info_weather",
                "Text": "🌤️ Погода",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply",
                "ActionBody": "info_news",
                "Text": "📰 Новости",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            },
            {
                "ActionType": "reply",
                "ActionBody": "back_to_main",
                "Text": "⬅️ Назад",
                "TextSize": "regular",
                "Columns": 2,
                "Rows": 1
            }
        ],
        "ButtonSize": "regular"
    }

def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    return user_id in AUTHORIZED_USER_IDS

@app.route('/webhook', methods=['GET', 'POST', 'HEAD'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "ok"})
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Получаем ID пользователя
            user_id = None
            if data.get('event') == 'message':
                user_id = data['sender']['id']
            elif data.get('event') == 'conversation_started':
                user_id = data['user']['id']
            
            # Проверяем авторизацию
            if user_id and not is_authorized_user(user_id):
                print(f"⛔ Unauthorized access attempt from: {user_id}")
                send_message(user_id, "❌ Доступ запрещен. Этот бот приватный.")
                return jsonify({"status": 0})
            
            # Обрабатываем сообщения только авторизованных пользователей
            if data.get('event') == 'message' and data['message']['type'] == 'text':
                message_text = data['message']['text'].lower()
                
                # Обработка навигации по меню
                menu_responses = {
                    # Главное меню
                    'меню': {
                        'text': '🏠 Главное меню\n\nВыберите нужную категорию:',
                        'keyboard': create_main_menu()
                    },
                    
                    # Крипто меню
                    'menu_crypto': {
                        'text': '₿ Криптовалюты\n\nВыберите действие:',
                        'keyboard': create_crypto_menu()
                    },
                    
                    # Инфо меню  
                    'menu_info': {
                        'text': 'ℹ️ Информация\n\nВыберите раздел:',
                        'keyboard': create_info_menu()
                    },
                    
                    # Тест Notion
                    'test_notion': {
                        'text': get_notion_test_message(),
                        'keyboard': create_main_menu()
                    },
                    
                    # Назад в главное меню
                    'back_to_main': {
                        'text': '🏠 Возвращаемся в главное меню',
                        'keyboard': create_main_menu()
                    },
                    
                    # Крипто функции
                    'crypto_view': {
                        'text': f'👁️ Просмотр курсов\n\n💰 Bitcoin: ${current_btc_price:,.2f}\n\n🔄 Обновляется каждые 30 секунд',
                        'keyboard': create_crypto_menu()
                    },
                    'crypto_months': {
                        'text': '📆 Статистика по месяцам\n\n💰 Bitcoin: данные по месяцам будут добавлены позже',
                        'keyboard': create_crypto_menu()
                    },
                    
                    # Инфо функции
                    'info_schedule': {
                        'text': '⏰ Расписание уведомлений\n\n🕒 Курс Bitcoin - каждые 30 секунд\n\n⏰ Дополнительные уведомления будут добавлены позже',
                        'keyboard': create_info_menu()
                    },
                    'info_weather': {
                        'text': '🌤️ Погода\n\nФункция погоды будет добавлена позже',
                        'keyboard': create_info_menu()
                    },
                    'info_news': {
                        'text': '📰 Новости\n\nФункция новостей будет добавлена позже',
                        'keyboard': create_info_menu()
                    },
                }
                
                # Проверяем команды меню
                if message_text in menu_responses:
                    menu_data = menu_responses[message_text]
                    send_message(user_id, menu_data['text'], menu_data['keyboard'])
                else:
                    # Обычные команды
                    responses = {
                        'привет': '👋 Привет! Это приватный крипто-бот!',
                        'портфель': '💰 Портфель: 1.2 BTC, 5.3 ETH',
                        'цена btc': f'📈 BTC: ${current_btc_price:,.2f}' if current_btc_price else '📈 Курс BTC временно недоступен',
                        'курс': f'💰 Текущий курс BTC: ${current_btc_price:,.2f}' if current_btc_price else '💰 Курс временно недоступен',
                        'команды': '🛠 Используйте кнопки меню или команды: привет, портфель, цена btc, курс, статус, btc, меню',
                        'мой id': f'🆔 Ваш ID: {user_id}',
                        'статус': '✅ Бот работает в штатном режиме с авто-обновлением курса BTC каждые 30 секунд',
                        'btc': f'₿ Bitcoin:\n💰 ${current_btc_price:,.2f}\n⏰ Обновляется каждые 30 секунд' if current_btc_price else '₿ Bitcoin: курс временно недоступен',
                        'меню': '🏠 Главное меню\n\nИспользуйте кнопки для навигации'
                    }
                    
                    response_text = responses.get(message_text, f'🤔 Не понял: {message_text}\n\n💡 Введите "меню" для открытия главного меню')
                    send_message(user_id, response_text, create_main_menu())
            
            elif data.get('event') == 'conversation_started':
                welcome_msg = """🔐 Добро пожаловать в приватный крипто-бот!

Я буду присылать вам курс Bitcoin каждые 30 секунд!

🏠 Используйте главное меню для навигации:
• ₿ Крипто - курсы и статистика
• ℹ️ Инфо - расписание, погода, новости
• 🧪 Тест Notion - проверка подключения к базе торговых данных

💰 Также доступны команды:
• цена btc - текущий курс
• курс - курс Bitcoin
• btc - информация о Bitcoin
• меню - открыть главное меню"""
                send_message(user_id, welcome_msg, create_main_menu())
            
            return jsonify({"status": 0})
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return jsonify({"status": 1})

def send_message(user_id, text, keyboard=None):
    """Отправляет сообщение пользователю через Viber API"""
    if not VIBER_TOKEN:
        print("❌ VIBER_TOKEN not set in environment variables")
        return False
        
    try:
        url = 'https://chatapi.viber.com/pa/send_message'
        headers = {
            'X-Viber-Auth-Token': VIBER_TOKEN,
            'Content-Type': 'application/json'
        }
        payload = {
            'receiver': user_id,
            'type': 'text',
            'text': text
        }
        
        # Добавляем клавиатуру если она есть
        if keyboard:
            payload['keyboard'] = keyboard
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 0:
                print(f"📤 Sent to {user_id[:8]}...: {text[:30]}...")
                return True
            else:
                print(f"❌ Viber API error: {result}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Send error: {e}")
        return False

@app.route('/status')
def status():
    """Эндпоинт для проверки статуса бота"""
    return jsonify({
        "status": "running",
        "btc_price": current_btc_price,
        "authorized_users": len(AUTHORIZED_USER_IDS),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Viber Crypto Bot...")
    print(f"📍 Port: {PORT}")
    print("⏰ BTC price updates will be sent every 30 seconds")
    
    # Получаем первоначальный курс BTC
    print("🔄 Getting initial BTC price...")
    initial_btc_data = get_btc_price()
    if initial_btc_data:
        current_btc_price = initial_btc_data['price']
        change_24h = initial_btc_data['change_24h']
        print(f"✅ Initial BTC price: ${current_btc_price:,.2f} | Change: {change_24h:.2f}%")
    else:
        print("❌ Failed to get initial BTC price")
    
    # Запускаем scheduler в отдельном потоке
    scheduler_thread = threading.Thread(target=btc_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ BTC scheduler started")
    
    # Запускаем Flask приложение
    print(f"🌐 Starting web server on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
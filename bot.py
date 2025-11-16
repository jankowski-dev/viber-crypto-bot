from flask import Flask, request, jsonify
import requests
import os
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)

VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
PORT = os.environ.get('PORT', 5000)

# Ваш User ID
AUTHORIZED_USER_IDS = [
    'zV/BRbzyPWJHKFpMTLWkqw=='
]

# Глобальная переменная для хранения последнего курса
current_btc_price = None
is_sending_enabled = True  # Флаг для управления отправкой

print("🤖 Private Viber Bot starting...")
print(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")

def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    return user_id in AUTHORIZED_USER_IDS

def get_btc_price():
    """Получает текущий курс биткоина с Binance"""
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return float(data['price'])
        else:
            print(f"❌ API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting BTC price: {e}")
        return None

def send_btc_price_update():
    """Отправляет обновление курса BTC авторизованным пользователям"""
    global current_btc_price, is_sending_enabled
    
    if not is_sending_enabled:
        print("⏸️ Sending is disabled")
        return
    
    print(f"🔄 Sending BTC update at {datetime.now().strftime('%H:%M:%S')}")
    
    price = get_btc_price()
    if price is not None:
        current_btc_price = price
        message = f"📊 BTC: ${price:,.2f}\n🕒 {datetime.now().strftime('%H:%M:%S')}"
        
        success_count = 0
        # Отправляем всем авторизованным пользователям
        for user_id in AUTHORIZED_USER_IDS:
            if send_message(user_id, message):
                success_count += 1
                print(f"📤 Sent BTC price to {user_id[:8]}...")
            else:
                print(f"❌ Failed to send to {user_id[:8]}...")
        
        print(f"✅ BTC update completed: {success_count}/{len(AUTHORIZED_USER_IDS)} users")
    else:
        print("❌ Failed to get BTC price")

def periodic_btc_sender():
    """Функция для периодической отправки курса (каждые 20 секунд)"""
    while True:
        try:
            send_btc_price_update()
            time.sleep(20)  # Ждем 20 секунд
        except Exception as e:
            print(f"❌ Error in periodic sender: {e}")
            time.sleep(20)  # При ошибке тоже ждем 20 секунд

def send_message(user_id, text):
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
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 0:
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

@app.route('/')
def home():
    """Главная страница"""
    global current_btc_price
    price_info = f"${current_btc_price:,.2f}" if current_btc_price else "N/A"
    
    return jsonify({
        "status": "ok",
        "message": "Viber Crypto Bot is running!",
        "btc_price": price_info,
        "authorized_users": len(AUTHORIZED_USER_IDS),
        "auto_sending": is_sending_enabled,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['GET', 'POST', 'HEAD'])
def webhook():
    """Основной вебхук для Viber"""
    if request.method == 'GET':
        return jsonify({"status": "ok"})
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(f"📨 Received webhook: {data.get('event', 'unknown')}")
            
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
                message_text = data['message']['text'].lower().strip()
                print(f"💬 Message from {user_id[:8]}...: {message_text}")
                
                responses = {
                    'привет': '👋 Привет! Это приватный крипто-бот!',
                    'портфель': '💰 Портфель: 1.2 BTC, 5.3 ETH',
                    'цена btc': f'📈 BTC: ${current_btc_price:,.2f}' if current_btc_price else '📈 Курс BTC временно недоступен',
                    'команды': '🛠 Команды: привет, портфель, цена btc, курс, статус',
                    'мой id': f'🆔 Ваш ID: {user_id}',
                    'курс': f'💰 Текущий курс BTC: ${current_btc_price:,.2f}' if current_btc_price else '💰 Курс временно недоступен',
                    'статус': '✅ Бот работает в штатном режиме с авто-обновлением курса'
                }
                
                response_text = responses.get(message_text, f'🤔 Не понял: "{message_text}"\n\nИспользуйте "команды" для списка доступных команд.')
                send_message(user_id, response_text)
                
            elif data.get('event') == 'conversation_started':
                welcome_msg = "🔐 Добро пожаловать в приватный крипто-бот!\n\n"
                welcome_msg += "Я буду присылать вам курс BTC каждые 20 секунд!\n"
                welcome_msg += "Используйте команду 'команды' для списка доступных команд."
                send_message(user_id, welcome_msg)
                print(f"🎉 Welcome message sent to {user_id[:8]}...")
            
            return jsonify({"status": 0})
            
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return jsonify({"status": 1})

@app.route('/btc')
def get_btc():
    """API endpoint для получения текущего курса BTC"""
    global current_btc_price
    price = get_btc_price()
    if price:
        current_btc_price = price
        return jsonify({
            "symbol": "BTCUSDT", 
            "price": price,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"error": "Failed to get BTC price"}), 500

@app.route('/status')
def status():
    """Статус бота"""
    return jsonify({
        "bot_status": "running",
        "btc_price": current_btc_price,
        "authorized_users": len(AUTHORIZED_USER_IDS),
        "auto_sending_enabled": is_sending_enabled,
        "last_update": datetime.now().isoformat()
    })

@app.route('/toggle-sending', methods=['POST'])
def toggle_sending():
    """Включить/выключить автоотправку"""
    global is_sending_enabled
    data = request.get_json() or {}
    is_sending_enabled = data.get('enabled', not is_sending_enabled)
    
    status_msg = "включена" if is_sending_enabled else "выключена"
    return jsonify({
        "message": f"Автоотправка {status_msg}",
        "enabled": is_sending_enabled
    })

def start_periodic_sender():
    """Запускает периодическую отправку курса в отдельном потоке"""
    sender_thread = threading.Thread(target=periodic_btc_sender, daemon=True)
    sender_thread.start()
    print("🚀 Periodic BTC sender started (every 20 seconds)")

if __name__ == '__main__':
    # Проверяем токен
    if not VIBER_TOKEN:
        print("❌ VIBER_TOKEN not set! Please set environment variable.")
        exit(1)
    
    # Первоначальное получение курса BTC
    print("🔄 Getting initial BTC price...")
    initial_price = get_btc_price()
    if initial_price:
        current_btc_price = initial_price
        print(f"✅ Initial BTC price: ${current_btc_price:,.2f}")
    else:
        print("❌ Failed to get initial BTC price")
    
    # Запускаем периодическую отправку
    start_periodic_sender()
    
    print(f"🚀 Starting Viber Bot on port {PORT}")
    print("⏰ BTC price updates will be sent every 20 seconds")
    print("💡 Use /status endpoint to check bot status")
    
    # Запускаем Flask приложение
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
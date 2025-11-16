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

def send_btc_updates():
    """Отправляет обновления курса BTC всем авторизованным пользователям"""
    global current_btc_price
    
    print(f"🔄 Sending BTC update at {datetime.now().strftime('%H:%M:%S')}")
    
    price = get_btc_price()
    if price is not None:
        current_btc_price = price
        timestamp = datetime.now().strftime('%H:%M:%S')
        message = f"📊 BTC: ${price:,.2f}\n🕒 {timestamp}\n\n💡 Обновляется каждые 30 секунд"
        
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

def btc_scheduler():
    """Фоновая задача для отправки курса BTC каждые 30 секунд"""
    while True:
        try:
            send_btc_updates()
            time.sleep(30)  # Каждые 30 секунд
        except Exception as e:
            print(f"❌ Error in BTC scheduler: {e}")
            time.sleep(30)  # При ошибке тоже ждем 30 секунд

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
                
                responses = {
                    'привет': '👋 Привет! Это приватный крипто-бот!',
                    'портфель': '💰 Портфель: 1.2 BTC, 5.3 ETH',
                    'цена btc': f'📈 BTC: ${current_btc_price:,.2f}' if current_btc_price else '📈 Курс BTC временно недоступен',
                    'курс': f'💰 Текущий курс BTC: ${current_btc_price:,.2f}' if current_btc_price else '💰 Курс временно недоступен',
                    'команды': '🛠 Команды: привет, портфель, цена btc, курс, статус',
                    'мой id': f'🆔 Ваш ID: {user_id}',
                    'статус': '✅ Бот работает в штатном режиме с авто-обновлением курса BTC каждые 30 секунд'
                }
                
                response_text = responses.get(message_text, f'🤔 Не понял: {message_text}')
                send_message(user_id, response_text)
            
            elif data.get('event') == 'conversation_started':
                send_message(user_id, "🔐 Добро пожаловать в приватный от!")
            
            return jsonify({"status": 0})
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return jsonify({"status": 1})

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
    initial_price = get_btc_price()
    if initial_price:
        current_btc_price = initial_price
        print(f"✅ Initial BTC price: ${current_btc_price:,.2f}")
    else:
        print("❌ Failed to get initial BTC price")
    
    # Запускаем scheduler в отдельном потоке
    scheduler_thread = threading.Thread(target=btc_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ BTC scheduler started")
    
    # Запускаем Flask приложение
    print(f"🌐 Starting web server on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
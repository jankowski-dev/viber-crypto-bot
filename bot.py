from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
PORT = os.environ.get('PORT', 5000)

# ⚠️ ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ USER_ID
AUTHORIZED_USER_IDS = [
    'zV/BRbzyPWJHKFpMTLWkqw=='  # ← ЗАМЕНИТЕ ЭТО на ваш реальный ID
]

print("🤖 Private Viber Bot starting...")
print(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")

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
                    'привет': '👋 Привет! Это приватный бот!',
                    'портфель': '💰 Портфель: 1.2 BTC, 5.3 ETH',
                    'цена btc': '📈 BTC: $61,500',
                    'команды': '🛠 Команды: привет, портфель, цена btc',
                    'мой id': f'🆔 Ваш ID: {user_id}'
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
    if not VIBER_TOKEN:
        return
        
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
        print(f"📤 Sent to {user_id[:8]}...: {text}")
        
    except Exception as e:
        print(f"❌ Send error: {e}")

if __name__ == '__main__':
    print(f"🚀 Starting on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
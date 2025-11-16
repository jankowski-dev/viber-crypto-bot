from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

# Получаем токен из переменных окружения Railway
VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
PORT = os.environ.get('PORT', 5000)

print("🤖 Viber Bot starting on Railway...")

@app.route('/')
def home():
    return "✅ Viber Bot is running on Railway!"

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    print(f"📨 Received {request.method} request")
    
    if request.method == 'GET':
        print("✅ GET request - webhook verification")
        return jsonify({"status": "ok", "message": "Webhook is working on Railway!"})
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(f"📝 POST data: {json.dumps(data, indent=2)}")
            
            # Обработка сообщений от пользователя
            if data.get('event') == 'message' and data['message']['type'] == 'text':
                user_id = data['sender']['id']
                message_text = data['message']['text'].lower()
                
                # Базовые команды бота
                if message_text == 'привет':
                    send_message(user_id, "👋 Привет! Я твой крипто-бот, работающий на Railway!")
                elif message_text == 'портфель':
                    send_message(user_id, "💰 Текущий портфель: 1.2 BTC, 5.3 ETH, 1000 USDT")
                elif message_text == 'цена btc':
                    send_message(user_id, "📈 BTC: $61,500 (данные из Notion)")
                elif message_text == 'команды':
                    send_message(user_id, "🛠 Доступные команды: привет, портфель, цена btc, команды")
                else:
                    send_message(user_id, f"🤔 Вы сказали: '{message_text}'. Используйте 'команды' для списка команд.")
            
            return jsonify({"status": "ok"})
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return jsonify({"status": "error", "message": str(e)})

def send_message(user_id, text):
    """Отправка сообщения пользователю через Viber API"""
    if not VIBER_TOKEN:
        print("❌ VIBER_TOKEN not set")
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
        print(f"📤 Sent to {user_id}: {text}")
        
        if response.status_code != 200:
            print(f"⚠️ Viber API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")

if __name__ == '__main__':
    print(f"🚀 Starting server on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
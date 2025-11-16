import requests
import os

# ⚠️ ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ
VIBER_TOKEN = "ваш_токен_из_viber"
RAILWAY_URL = "https://ваш-проект.up.railway.app"  # Замените на ваш URL после деплоя

def setup_webhook():
    webhook_url = f"{RAILWAY_URL}/webhook"
    
    print("🌐 Setting up webhook for Railway...")
    print(f"📍 Webhook URL: {webhook_url}")
    print(f"🔑 Token: {VIBER_TOKEN[:15]}...")  # Показываем только начало токена
    
    url = 'https://chatapi.viber.com/pa/set_webhook'
    headers = {
        'X-Viber-Auth-Token': VIBER_TOKEN,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "url": webhook_url,
        "event_types": [
            "delivered", "seen", "failed", 
            "subscribed", "unsubscribed", "conversation_started",
            "message"
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        result = response.json()
        print("🔧 Response from Viber:", result)
        
        if result.get('status') == 0:
            print("🎉 WEBHOOK SETUP SUCCESSFUL!")
            print("🚀 You can now talk to your bot in Viber!")
        else:
            print(f"❌ Error: {result.get('status_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Critical error: {e}")

if __name__ == '__main__':
    setup_webhook()
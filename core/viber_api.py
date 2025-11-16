import requests
from config.settings import VIBER_TOKEN

def send_message(user_id, text):
    """Отправляет сообщение пользователю через Viber API"""
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
        print(f"📤 Sent to {user_id[:8]}...: {text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Send error: {e}")
        return False

def send_message_to_admin(text):
    """Отправляет сообщение администратору бота"""
    from config.settings import BOT_CONFIG
    admin_id = BOT_CONFIG.get('admin_id')
    if admin_id:
        return send_message(admin_id, text)
    return False
from config.settings import AUTHORIZED_USER_IDS

def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    return user_id in AUTHORIZED_USER_IDS

def get_user_from_request(data):
    """Извлекает user_id из запроса Viber"""
    user_id = None
    
    if data.get('event') == 'message':
        user_id = data['sender']['id']
    elif data.get('event') == 'conversation_started':
        user_id = data['user']['id']
    
    return user_id

def log_unauthorized_access(user_id):
    """Логирует попытку неавторизованного доступа"""
    print(f"⛔ Unauthorized access attempt from: {user_id}")
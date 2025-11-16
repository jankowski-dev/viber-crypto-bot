import os

# Настройки Viber
VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
PORT = os.environ.get('PORT', 5000)

# Авторизованные пользователи
AUTHORIZED_USER_IDS = [os.environ.get('USER_TOKEN')]

# Настройки бота
BOT_CONFIG = {
    'name': 'Crypto Bot',
    'version': '1.0.0',
    'admin_id': AUTHORIZED_USER_IDS[0] if AUTHORIZED_USER_IDS else None
}
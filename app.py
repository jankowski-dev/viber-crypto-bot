from flask import Flask, request, jsonify
from config.settings import PORT, BOT_CONFIG
from core.auth import is_authorized_user, get_user_from_request, log_unauthorized_access
from core.viber_api import send_message
from handlers.message_handlers import EventHandler
from utils.helpers import setup_logging

app = Flask(__name__)

# Настройка логирования
setup_logging()

print(f"🤖 {BOT_CONFIG['name']} v{BOT_CONFIG['version']} starting...")

@app.route('/')
def home():
    """Главная страница для проверки работы"""
    return jsonify({
        "status": "ok", 
        "bot": BOT_CONFIG['name'],
        "version": BOT_CONFIG['version']
    })

@app.route('/webhook', methods=['GET', 'POST', 'HEAD'])
def webhook():
    """Основной вебхук для Viber"""
    if request.method == 'GET':
        return jsonify({"status": "ok"})
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Проверяем авторизацию пользователя
            user_id = get_user_from_request(data)
            if user_id and not is_authorized_user(user_id):
                log_unauthorized_access(user_id)
                send_message(user_id, "❌ Доступ запрещен. Этот бот приватный.")
                return jsonify({"status": 0})
            
            # Передаем событие в обработчик
            if user_id:
                EventHandler.handle_event(data)
            
            return jsonify({"status": 0})
            
        except Exception as e:
            print(f"❌ Error processing webhook: {e}")
            return jsonify({"status": 1})

@app.route('/health')
def health_check():
    """Эндпоинт для проверки здоровья приложения"""
    return jsonify({
        "status": "healthy",
        "timestamp": get_current_time(),
        "bot": BOT_CONFIG['name']
    })

if __name__ == '__main__':
    print(f"🚀 Starting {BOT_CONFIG['name']} on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
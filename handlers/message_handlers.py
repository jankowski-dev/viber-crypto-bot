from core.viber_api import send_message

class MessageHandler:
    """Обработчик текстовых сообщений"""
    
    @staticmethod
    def handle_text_message(user_id, message_text):
        """Обрабатывает текстовые сообщения от пользователя"""
        message_text = message_text.lower()
        
        # Базовая логика ответов
        responses = {
            'привет': '👋 Привет! Это приватный бот!',
            'портфель': '💰 Портфель: 1.2 BTC, 5.3 ETH',
            'цена btc': '📈 BTC: $61,500',
            'команды': '🛠 Команды: привет, портфель, цена btc',
            'мой id': f'🆔 Ваш ID: {user_id}',
            'статус': '✅ Бот работает в штатном режиме'
        }
        
        response_text = responses.get(message_text, f'🤔 Не понял: {message_text}')
        return send_message(user_id, response_text)
    
    @staticmethod
    def handle_conversation_started(user_id):
        """Обрабатывает начало диалога"""
        return send_message(user_id, "🔐 Добро пожаловать в приватный бот!")

class EventHandler:
    """Обработчик событий Viber"""
    
    @staticmethod
    def handle_event(data):
        """Роутит события по соответствующим обработчикам"""
        event_type = data.get('event')
        
        if event_type == 'message' and data['message']['type'] == 'text':
            user_id = data['sender']['id']
            message_text = data['message']['text']
            return MessageHandler.handle_text_message(user_id, message_text)
        
        elif event_type == 'conversation_started':
            user_id = data['user']['id']
            return MessageHandler.handle_conversation_started(user_id)
        
        return False
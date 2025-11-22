from flask import Flask, request, jsonify
import requests
import os
import logging

# --- Импорт функций из нового модуля ---
from notion_client import check_notion_connection, get_quick_report, get_wide_report

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

# --- Настройки ---
VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')  # Токен интеграции
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')  # ID базы данных
PORT = os.environ.get('PORT', 5000)

# Ваши авторизованные ID пользователей
AUTHORIZED_USER_IDS = [
    'zV/BRbzyPWJHKFpMTLWkqw=='  # ЗАМЕНИТЕ на ваш реальный ID
]

logger.info("🤖 Private Viber Bot with Notion Integration starting...")
logger.info(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")
logger.info(f"📊 Notion DB ID: {NOTION_DATABASE_ID[-8:] if NOTION_DATABASE_ID else 'Not set'}...")


def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    auth_result = user_id in AUTHORIZED_USER_IDS
    logger.debug(f"Authorization check for {user_id}: {auth_result}")
    return auth_result


def send_message_with_keyboard(user_id, text, keyboard=None):
    """Отправляет сообщение с опциональной клавиатурой (меню)."""
    if not VIBER_TOKEN:
        logger.error("VIBER_TOKEN not set.")
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
        if keyboard:
            payload['keyboard'] = keyboard
            logger.info(f"Sending message with keyboard to {user_id[:8]}...")

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info(f"📤 Sent to {user_id[:8]}...: {text[:50]}...")
        else:
            logger.error(f"❌ Send failed with status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"❌ Send error: {e}")


def get_main_menu_keyboard():
    """Создает клавиатуру для главного меню."""
    return {
        "Type": "keyboard",
        "DefaultHeight": True,
        "Buttons": [
            {
                "ActionType": "reply",
                "ActionBody": "crypto_menu",
                "Text": "🪙 Крипто"
            },
            {
                "ActionType": "reply",
                "ActionBody": "help_info",
                "Text": "❓ Помощь"
            }
        ]
    }


def get_crypto_menu_keyboard():
    """Создает клавиатуру для подменю Крипто."""
    # Добавлена кнопка 'wide_report'
    return {
        "Type": "keyboard",
        "DefaultHeight": True,
        "Buttons": [
            {
                "ActionType": "reply",
                "ActionBody": "quick_report",
                "Text": "📉 Быстрый отчет"
            },
            {
                "ActionType": "reply",
                "ActionBody": "wide_report",
                "Text": "📊 Широкий отчет"
            },
            {
                "ActionType": "reply",
                "ActionBody": "back_to_main",
                "Text": "🔙 Назад"
            }
        ]
    }


@app.route('/webhook', methods=['GET', 'POST', 'HEAD'])
def webhook():
    logger.info("--- Webhook received ---")
    if request.method == 'GET':
        logger.info("Received GET request.")
        return jsonify({"status": "ok"})

    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.info(f"Full webhook data: {data}")
            user_id = None
            message_text = None
            sender_name = data.get('sender', {}).get('name', 'Unknown')
            event_type = data.get('event')
            logger.info(f"Event type: {event_type}")

            if event_type == 'message':
                logger.info("Processing 'message' event.")
                user_id = data.get('sender', {}).get('id')
                logger.info(f"User ID from sender: {user_id}")
                if data['message']['type'] == 'text':
                    message_text = data['message']['text'].lower()
                    logger.info(f"Message text: {message_text}")
                else:
                    logger.info(f"Non-text message type: {data['message']['type']}")
                    return jsonify({"status": 0})

            elif event_type == 'conversation_started':
                logger.info("Processing 'conversation_started' event.")
                user_id = data.get('user', {}).get('id')  # Для conversation_started используем 'user'
                logger.info(f"User ID from user: {user_id}")
                # Отправляем главное меню при начале разговора
                if user_id:
                    logger.info(f"Sending main menu to {user_id} on conversation start.")
                    send_message_with_keyboard(user_id, f"🔐 Добро пожаловать, {sender_name}! Используйте меню.", get_main_menu_keyboard())
                return jsonify({"status": 0})

            elif event_type in ['subscribed', 'unsubscribed', 'failed', 'seen', 'delivered']:
                # Эти события не требуют ответа от бота, но логируем их
                logger.info(f"Received event '{event_type}' which does not require processing.")
                return jsonify({"status": 0})

            else:
                logger.warning(f"Unknown event type: {event_type}")
                return jsonify({"status": 0})

            if not user_id:
                logger.warning("No user_id found in webhook data after processing event.")
                return jsonify({"status": 0})

            logger.info(f"Final user_id for processing: {user_id}")

            if not is_authorized_user(user_id):
                logger.info(f"⛔ Unauthorized access attempt from: {user_id}")
                send_message_with_keyboard(user_id, "❌ Доступ запрещен. Этот бот приватный.")
                return jsonify({"status": 0})

            action_body = data.get('message', {}).get('text')  # Для кнопок, текст = ActionBody
            logger.info(f"Action body (from message.text): {action_body}")

            if action_body:
                if action_body == "crypto_menu":
                    logger.info("Handling 'crypto_menu' action.")
                    send_message_with_keyboard(user_id, "Выберите действие в Крипто:", get_crypto_menu_keyboard())
                elif action_body == "help_info":
                    logger.info("Handling 'help_info' action.")
                    send_message_with_keyboard(user_id, "🤖 Это приватный бот.\nИспользуйте меню для навигации.")
                elif action_body == "back_to_main":
                    logger.info("Handling 'back_to_main' action.")
                    send_message_with_keyboard(user_id, "Возврат в главное меню.", get_main_menu_keyboard())
                elif action_body == "quick_report":
                    logger.info("Handling 'quick_report' action. Fetching and analyzing data from Notion...")
                    # Вызываем функцию получения быстрого отчета из notion_client
                    report_message = get_quick_report()
                    # Отправляем пользователю результат
                    send_message_with_keyboard(user_id, report_message, get_crypto_menu_keyboard())  # Возвращаем к подменю после отчета
                elif action_body == "wide_report":
                    logger.info("Handling 'wide_report' action. Fetching and analyzing data from Notion...")
                    # Вызываем функцию получения широкого отчета из notion_client
                    report_message = get_wide_report()
                    # Отправляем пользователю результат
                    send_message_with_keyboard(user_id, report_message, get_crypto_menu_keyboard())  # Возвращаем к подменю после отчета
                else:
                    logger.info(f"Unknown action body: {action_body}")
                    # Возможно, это текстовое сообщение, не связанное с меню
                    if message_text:  # Проверяем, было ли это текстовое сообщение
                        logger.info(f"Received unknown action body, treating as text command: {message_text}")
                        # Можно добавить обработку старых команд или игнорировать
                        send_message_with_keyboard(user_id, f"🤔 Неизвестная команда: {message_text}", get_main_menu_keyboard())

            logger.info("--- Webhook processing finished ---")
            return jsonify({"status": 0})
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            logger.exception("Full traceback:")  # Логируем полный стек вызовов
            return jsonify({"status": 1})


def send_message(user_id, text):  # Оставлена для совместимости
    send_message_with_keyboard(user_id, text)


if __name__ == '__main__':
    logger.info(f"🚀 Starting on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)

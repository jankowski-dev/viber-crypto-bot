from flask import Flask, request, jsonify
import requests
import os
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Настройки ---
VIBER_TOKEN = os.environ.get('VIBER_TOKEN')
NOTION_TOKEN = os.environ.get('NOTION_TOKEN') # Токен интеграции
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID') # ID базы данных
PORT = os.environ.get('PORT', 5000)

# Ваши авторизованные ID пользователей
AUTHORIZED_USER_IDS = [
    'zV/BRbzyPWJHKFpMTLWkqw=='  # ЗАМЕНИТЕ на ваш реальный ID
]

logger.info("🤖 Private Viber Bot with Notion Integration (HTTP API) starting...")
logger.info(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")
logger.info(f"📊 Notion DB ID: {NOTION_DATABASE_ID[-8:] if NOTION_DATABASE_ID else 'Not set'}...")

def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    auth_result = user_id in AUTHORIZED_USER_IDS
    logger.debug(f"Authorization check for {user_id}: {auth_result}")
    return auth_result

def get_crypto_data_from_notion_http():
    """Извлекает данные из Notion DB с помощью HTTP API. Возвращает список словарей."""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logger.error("Notion credentials (NOTION_TOKEN or NOTION_DATABASE_ID) not set.")
        return None, "Ошибка: Не заданы учетные данные для Notion."

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28" # Указываем версию API
    }

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {} # Можно добавить фильтры или сортировку сюда

    try:
        logger.info("Sending query to Notion API...")
        response = requests.post(url, headers=headers, json=payload, timeout=15) # POST запрос для query
        response.raise_for_status() # Возбуждает исключение для 4xx/5xx статусов

        data = response.json()
        pages = data.get("results", [])
        logger.info(f"Received {len(pages)} pages from Notion.")
        parsed_data = []

        for page in pages:
            page_id = page["id"] # ID страницы (строки), может понадобиться позже
            props = page.get("properties", {})

            # --- Извлечение свойств с использованием точных имен из notion_properties_mapping.txt ---
            # Свойство: 'Прибыльные сделки Rollup' (Тип: rollup, ID: %3A%3A%5BW)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            profit_making_trades_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Ср. доходность, %' (Тип: rollup, ID: %3A%3DWF)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            avg_yield_pct_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Депозит, %' (Тип: formula, ID: %3FpZT)
            deposit_pct_prop = props.get("Депозит, %", {})
            deposit_pct_formula_obj = deposit_pct_prop.get("formula", {})
            deposit_pct_value = deposit_pct_formula_obj.get("number", deposit_pct_formula_obj.get("string", deposit_pct_formula_obj.get("date", "N/A")))

            # Свойство: 'Комиссии' (Тип: rollup, ID: CkpA)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            fees_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Прибыль / Убыток' (Тип: rollup, ID: DM%3Ac)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            profit_loss_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Оборот открытых Rollup' (Тип: rollup, ID: DomP)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            open_turnover_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Текущая' (Тип: rollup, ID: Jl%7D%5D)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            current_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Капитализация, $' (Тип: rollup, ID: Js%7CC)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            capitalization_usd_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Текущая прибыль' (Тип: formula, ID: Zp%5Bd)
            current_profit_prop = props.get("Текущая прибыль", {})
            current_profit_formula_obj = current_profit_prop.get("formula", {})
            current_profit_value = current_profit_formula_obj.get("number", current_profit_formula_obj.get("string", current_profit_formula_obj.get("date", "N/A")))

            # Свойство: 'Cделки +' (Тип: formula, ID: %5Be%3E%3C)
            deals_plus_prop = props.get("Cделки +", {})
            deals_plus_formula_obj = deals_plus_prop.get("formula", {})
            deals_plus_value = deals_plus_formula_obj.get("number", deals_plus_formula_obj.get("string", deals_plus_formula_obj.get("date", "N/A")))

            # Свойство: 'Текущий курс' (Тип: rollup, ID: %5BlCP)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            current_price_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Формула прибыли' (Тип: formula, ID: cs%60X)
            profit_formula_prop = props.get("Формула прибыли", {})
            profit_formula_formula_obj = profit_formula_prop.get("formula", {})
            profit_formula_value = profit_formula_formula_obj.get("number", profit_formula_formula_obj.get("string", profit_formula_formula_obj.get("date", "N/A")))

            # Свойство: 'Чистая прибыль Rollup' (Тип: rollup, ID: e%3B%3Fy)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            net_profit_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Доходность, %' (Тип: formula, ID: fy%3F%5E)
            yield_pct_prop = props.get("Доходность, %", {})
            yield_pct_formula_obj = yield_pct_prop.get("formula", {})
            yield_pct_value = yield_pct_formula_obj.get("number", yield_pct_formula_obj.get("string", yield_pct_formula_obj.get("date", "N/A")))

            # Свойство: 'Оборот закрытых Rollup' (Тип: rollup, ID: kBOl)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            closed_turnover_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Чистая прибыль' (Тип: formula, ID: kBU%60)
            net_profit_prop = props.get("Чистая прибыль", {})
            net_profit_formula_obj = net_profit_prop.get("formula", {})
            net_profit_value = net_profit_formula_obj.get("number", net_profit_formula_obj.get("string", net_profit_formula_obj.get("date", "N/A")))

            # Свойство: 'Date' (Тип: date, ID: laaW)
            date_prop = props.get("Date", {})
            date_date_obj = date_prop.get("date", {})
            date_value = date_date_obj.get("start", "N/A") if date_date_obj else "N/A"

            # Свойство: 'Ср. срок Rollup' (Тип: rollup, ID: luu%7B)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            avg_duration_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Криптосчет' (Тип: relation, ID: o%3CpV)
            # Тип 'relation' неизвестен. Проверьте документацию Notion API.
            crypto_account_relation_value = 'Тип неизвестен (Relation)'

            # Свойство: 'Активных' (Тип: rollup, ID: qOe%40)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            active_count_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Оборот' (Тип: formula, ID: u%40A%3E)
            turnover_prop = props.get("Оборот", {})
            turnover_formula_obj = turnover_prop.get("formula", {})
            turnover_value = turnover_formula_obj.get("number", turnover_formula_obj.get("string", turnover_formula_obj.get("date", "N/A")))

            # Свойство: 'Оборотные, $' (Тип: formula, ID: yIzH)
            turnover_usd_prop = props.get("Оборотные, $", {})
            turnover_usd_formula_obj = turnover_usd_prop.get("formula", {})
            turnover_usd_value = turnover_usd_formula_obj.get("number", turnover_usd_formula_obj.get("string", turnover_usd_formula_obj.get("date", "N/A")))

            # Свойство: 'Ср. срок' (Тип: formula, ID: zAfo)
            avg_duration_prop = props.get("Ср. срок", {})
            avg_duration_formula_obj = avg_duration_prop.get("formula", {})
            avg_duration_value = avg_duration_formula_obj.get("number", avg_duration_formula_obj.get("string", avg_duration_formula_obj.get("date", "N/A")))

            # Свойство: 'Средний курс' (Тип: formula, ID: %7DwU%5E)
            avg_price_prop = props.get("Средний курс", {})
            avg_price_formula_obj = avg_price_prop.get("formula", {})
            avg_price_value = avg_price_formula_obj.get("number", avg_price_formula_obj.get("string", avg_price_formula_obj.get("date", "N/A")))

            # Свойство: 'Оборот, мон.' (Тип: rollup, ID: ~%3Dk%5B)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            turnover_coins_rollup_value = 'Тип неизвестен (Rollup)'

            # Свойство: '' (Тип: title, ID: title) - Пустое имя, предположим это заголовок
            # ВНИМАНИЕ: Пустое имя свойства может вызвать проблемы. Лучше дать ему имя в Notion.
            # Для примера, если это заголовок, и вы его назовете "Name", используйте:
            # name_prop = props.get("Name", {})
            # name_title_array = name_prop.get("title", [])
            # name_value = name_title_array[0].get("text", {}).get("content", "N/A") if name_title_array else "N/A"
            # Пока оставим как есть, но рекомендуется исправить в Notion.
            name_prop = props.get("", {}) # Используем пустую строку как ключ
            name_title_array = name_prop.get("title", [])
            name_value = name_title_array[0].get("text", {}).get("content", "N/A (Без имени)") if name_title_array else "N/A (Без имени)"


            # --- Сбор данных в словарь ---
            # Здесь вы можете выбрать, какие именно свойства использовать в отчетах.
            # Я выбрал несколько, соответствующие вашим требованиям.
            parsed_data.append({
                "page_id": page_id,
                "name": name_value, # Используем значение заголовка (или "N/A (Без имени)")
                "current_profit": current_profit_value, # Может быть числом, строкой или None
                "capitalization": capitalization_usd_value, # Rollup - строка
                "turnover": turnover_value, # Formula - может быть числом или строкой
                "deposit_pct": deposit_pct_value, # Formula - может быть числом или строкой
                "avg_price": avg_price_value, # Formula - может быть числом или строкой
                "current_price": current_price_rollup_value, # Rollup - строка
                # Можно добавить и другие, если понадобятся
                # "other_prop": other_value,
            })

        logger.info(f"Parsed data successfully: {len(parsed_data)} items.")
        return parsed_data, None

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        logger.error(f"Response content: {response.text}")
        return None, f"Ошибка HTTP при запросе к Notion: {http_err}"
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        return None, f"Ошибка запроса к Notion: {req_err}"
    except Exception as e:
        logger.error(f"Unexpected error parsing Notion  {e}")
        return None, f"Неизвестная ошибка при обработке данных Notion: {e}"


def format_quick_report(data):
    """Формирует строку быстрого отчета, исключая записи с нулевой прибылью/убытком."""
    if not data:
        return "❌ Не удалось получить данные для отчета."
    
    # Фильтрация данных: оставляем только те, у которых current_profit не является 0, 0.0, "0", "0.0" или None
    filtered_data = []
    for item in 
        profit = item.get('current_profit', 0)
        # Проверяем, является ли значение "нулевым" числом (0 или 0.0) или строкой "0"/"0.0"
        if profit is not None and profit != 0 and profit != 0.0 and profit != "0" and profit != "0.0":
            filtered_data.append(item)
        # else:
        #     logger.debug(f"Filtering out item: {item.get('name', 'N/A')} with profit: {profit}")

    if not filtered_
        return "📉 Нет криптосчетов с ненулевой прибылью/убытком для отчета."

    report_lines = ["📈 Быстрый отчет по криптосчетам:\n"]
    total_profit = 0
    for item in 
        profit = item.get('current_profit', 0)
        # Проверяем, является ли значение числом, прежде чем складывать и форматировать
        if profit is not None and isinstance(profit, (int, float)):
             total_profit += profit
             formatted_profit = f"{profit:.2f}"
        else:
            # Если не число, используем строковое представление
            formatted_profit = str(profit) if profit is not None else "N/A"

        # Выводим название криптосчета
        report_lines.append(f"- {item.get('name', 'N/A')}: {formatted_profit}")

    # Вычисляем форматированную строку для total_profit отдельно
    formatted_total_profit = f"{total_profit:.2f}" if isinstance(total_profit, (int, float)) else str(total_profit)
    report_lines.append(f"\n💰 Сумма текущей прибыли/убытка: {formatted_total_profit}")
    return "\n".join(report_lines)


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
    # Удалена кнопка 'wide_report'
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
            logger.info(f"Full webhook  {data}")

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
                user_id = data.get('user', {}).get('id') # Для conversation_started используем 'user'
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

            action_body = data.get('message', {}).get('text') # Для кнопок, текст = ActionBody
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
                     logger.info("Handling 'quick_report' action.")
                     crypto_data, error = get_crypto_data_from_notion_http()
                     if error:
                         logger.error(f"Error fetching data for quick report: {error}")
                         send_message_with_keyboard(user_id, error)
                     else:
                         report = format_quick_report(crypto_data)
                         send_message_with_keyboard(user_id, report, get_crypto_menu_keyboard()) # Возвращаем к подменю после отчета
                 # Удалена обработка 'wide_report'
                 else:
                     logger.info(f"Unknown action body: {action_body}")
                     # Возможно, это текстовое сообщение, не связанное с меню
                     if message_text: # Проверяем, было ли это текстовое сообщение
                         logger.info(f"Received unknown action body, treating as text command: {message_text}")
                         # Можно добавить обработку старых команд или игнорировать
                         send_message_with_keyboard(user_id, f"🤔 Неизвестная команда: {message_text}", get_main_menu_keyboard())

            logger.info("--- Webhook processing finished ---")
            return jsonify({"status": 0})

        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            logger.exception("Full traceback:") # Логируем полный стек вызовов
            return jsonify({"status": 1})

def send_message(user_id, text): # Оставлена для совместимости
    send_message_with_keyboard(user_id, text)

if __name__ == '__main__':
    logger.info(f"🚀 Starting on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
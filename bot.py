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
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') # API ключ для support.by
OPENAI_API_URL = "https://global.support.by/api/openai/v1/chat/completions" # URL эндпоинта support.by
PORT = os.environ.get('PORT', 5000)

# Ваши авторизованные ID пользователей
AUTHORIZED_USER_IDS = [
    'zV/BRbzyPWJHKFpMTLWkqw=='  # ЗАМЕНИТЕ на ваш реальный ID
]

logger.info("🤖 Private Viber Bot with Notion Integration (via AI) starting...")
logger.info(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")
logger.info(f"📊 Notion DB ID: {NOTION_DATABASE_ID[-8:] if NOTION_DATABASE_ID else 'Not set'}...")
# --- ИЗМЕНЕНО: Сообщение об используемой модели ---
logger.info(f"🧠 Using AI API: {OPENAI_API_URL} (Model: deepseek-chat)")

def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    auth_result = user_id in AUTHORIZED_USER_IDS
    logger.debug(f"Authorization check for {user_id}: {auth_result}")
    return auth_result

def get_raw_crypto_data_from_notion_http():
    """Извлекает *сырые* данные из Notion DB с помощью HTTP API. Возвращает список словарей."""
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

            # --- Извлечение *всех* нужных свойств из notion_properties_mapping.txt ---
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

            # --- ИСПРАВЛЕНО: Извлечение значения из 'Текущая' (Тип: rollup, ID: Jl%7D%5D) ---
            текущая_prop = props.get("Текущая", {})
            # Для rollup типа number, строка или date, извлекаем соответствующее значение
            # Обычно rollup number возвращает словарь с ключом 'number'
            # Если current_prop сам по себе словарь с ключом 'number', 'string', 'date', нужно проверить это
            текущая_rollup_obj = "N/A" # Значение по умолчанию
            if isinstance(текущая_prop, dict):
                # Проверим структуру ответа для rollup
                # Пример структуры для rollup number: {"type": "number", "number": 123.45}
                # Пример структуры для rollup string: {"type": "string", "string": "some text"}
                rollup_type = текущая_prop.get("type")
                if rollup_type == "number":
                    текущая_rollup_obj = текущая_prop.get("number", "N/A")
                elif rollup_type == "string":
                    текущая_rollup_obj = текущая_prop.get("string", "N/A")
                elif rollup_type == "date":
                    # Извлекаем start или end из объекта даты
                    date_obj = текущая_prop.get("date", {})
                    текущая_rollup_obj = date_obj.get("start", "N/A") if date_obj else "N/A"
                else:
                    # Если тип не number/string/date, или структура другая
                    текущая_rollup_obj = "N/A (Тип неизвестен)"
            else:
                # Если текущая_prop не словарь, значит он сам является значением (редкий случай)
                текущая_rollup_obj = текущая_prop


            # Свойство: 'Капитализация, $' (Тип: rollup, ID: Js%7CC)
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            capitalization_usd_value = 'Тип неизвестен (Rollup)'

            # Свойство: 'Текущая прибыль' (Тип: formula, ID: Zp%5Bd)
            текущая_прибыль_prop = props.get("Текущая прибыль", {})
            текущая_прибыль_formula_obj = текущая_прибыль_prop.get("formula", {})
            текущая_прибыль_value = текущая_прибыль_formula_obj.get("number", текущая_прибыль_formula_obj.get("string", текущая_прибыль_formula_obj.get("date", "N/A")))

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


            # --- Сбор *всех* данных в словарь ---
            # Эти данные будут отправлены ИИ для анализа
            parsed_data.append({
                "page_id": page_id,
                "name": name_value, # Используем значение заголовка (или "N/A (Без имени)")
                "current_profit_raw": текущая_rollup_obj, # <-- Используем значение из 'Текущая' (число, строка, N/A)
                "capitalization": capitalization_usd_value, # Rollup - строка
                "turnover": turnover_value, # Formula - может быть числом или строкой
                "deposit_pct": deposit_pct_value, # Formula - может быть числом или строкой
                "avg_price": avg_price_value, # Formula - может быть числом или строкой
                "current_price": current_price_rollup_value, # Rollup - строка
                # Можно добавить и другие, если понадобятся
                # "other_prop": other_value,
            })

        logger.info(f"Raw data parsed successfully: {len(parsed_data)} items.")
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


def send_data_to_ai_api(raw_data):
    """Отправляет *сырые* данные в ИИ API и возвращает сформированный отчет."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set.")
        return "❌ Ошибка: Не задан API-ключ для ИИ."

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Формируем сообщение для ИИ
    # Промпт: Опишите, что ИИ должен сделать с raw_data
    # --- ИЗМЕНЕНО: Убрана роль 'developer', добавлена инструкция в сообщение 'user', модель 'deepseek-chat' ---
    user_message_content = (
        "You are a helpful assistant.\n\n"
        "Проанализируй следующие данные криптосчетов. "
        "Отфильтруй те, у которых 'current_profit_raw' равен 0, 0.0, '0', '0.0', None или NaN. "
        "Для оставшихся счетов выведи название ('name') и значение 'current_profit_raw'. "
        "Также посчитай общую сумму прибыли/убытка по оставшимся счетам. "
        "Форматируй ответ как список криптосчетов с их прибылью/убытком и итоговую сумму в конце.\n\n"
        f"Данные: {json.dumps(raw_data, ensure_ascii=False, indent=2)}"
    )

    payload = {
        "model": "deepseek-chat", # --- ИЗМЕНЕНО: Указана модель deepseek-chat ---
        "messages": [
            {
                "role": "user", # --- ИЗМЕНЕНО: Используем только 'user' ---
                "content": user_message_content
            }
        ],
        "temperature": 0.1 # Низкая температура для более детерминированного результата
    }

    try:
        logger.info("Sending data to AI API...")
        # --- ИЗМЕНЕНО: Увеличен таймаут до 60 секунд ---
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=60) 
        response.raise_for_status()

        ai_response = response.json()
        # Извлекаем сгенерированный текст из ответа
        report_text = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '❌ Не удалось сгенерировать отчет.')
        logger.info("Report received from AI API.")
        return report_text

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while calling AI API: {http_err}")
        logger.error(f"Response content: {response.text}")
        return f"❌ Ошибка HTTP при запросе к ИИ: {http_err}"
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred while calling AI API: {req_err}")
        # --- ИЗМЕНЕНО: Уточнение типа ошибки ---
        if isinstance(req_err, requests.exceptions.ReadTimeout):
            logger.error("AI API request timed out.")
            return f"❌ Таймаут запроса к ИИ: сервер не ответил за 60 секунд."
        return f"❌ Ошибка запроса к ИИ: {req_err}"
    except Exception as e:
        logger.error(f"Unexpected error calling AI API: {e}")
        return f"❌ Неизвестная ошибка при запросе к ИИ: {e}"


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
                     # Шаг 1: Получить *сырые* данные из Notion
                     raw_data, error = get_raw_crypto_data_from_notion_http()
                     if error:
                         logger.error(f"Error fetching raw data for quick report: {error}")
                         send_message_with_keyboard(user_id, error)
                     else:
                         # Шаг 2: Отправить *сырые* данные в ИИ API
                         ai_report = send_data_to_ai_api(raw_data)
                         if ai_report.startswith("❌"):
                             logger.error(f"Error from AI API: {ai_report}")
                             send_message_with_keyboard(user_id, ai_report)
                         else:
                             # Шаг 3: Отправить сгенерированный ИИ отчет пользователю
                             send_message_with_keyboard(user_id, ai_report, get_crypto_menu_keyboard()) # Возвращаем к подменю после отчета
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
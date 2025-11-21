from flask import Flask, request, jsonify
import requests
import os
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
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

print("🤖 Private Viber Bot with Notion Integration (HTTP API) starting...")
print(f"🔐 Authorized users: {len(AUTHORIZED_USER_IDS)}")
print(f"📊 Notion DB ID: {NOTION_DATABASE_ID[-8:] if NOTION_DATABASE_ID else 'Not set'}...")

def is_authorized_user(user_id):
    """Проверяет, авторизован ли пользователь"""
    return user_id in AUTHORIZED_USER_IDS

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
        response = requests.post(url, headers=headers, json=payload, timeout=15) # POST запрос для query
        response.raise_for_status() # Возбуждает исключение для 4xx/5xx статусов

        data = response.json()
        pages = data.get("results", [])
        parsed_data = []

        for page in pages:
            page_id = page["id"] # ID страницы (строки), может понадобиться позже
            props = page.get("properties", {})

            # --- Извлечение свойств с использованием точных имен из notion_properties_mapping.txt ---
            # Свойство: 'Прибыльные сделки Rollup' (Тип: rollup, ID: %3A%3A%5BW)
            прибыльные_сделки_rollup_prop = props.get("Прибыльные сделки Rollup", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            прибыльные_сделки_rollup_value = 'Тип неизвестен'

            # Свойство: 'Ср. доходность, %' (Тип: rollup, ID: %3A%3DWF)
            ср._доходность,_%_prop = props.get("Ср. доходность, %", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            ср._доходность,_%_value = 'Тип неизвестен'

            # Свойство: 'Депозит, %' (Тип: formula, ID: %3FpZT)
            депозит,_%_prop = props.get("Депозит, %", {})
            депозит,_%_formula_obj = депозит,_%_prop.get("formula", {})
            депозит,_%_value = депозит,_%_formula_obj.get("number", депозит,_%_formula_obj.get("string", депозит,_%_formula_obj.get("date", "N/A")))

            # Свойство: 'Комиссии' (Тип: rollup, ID: CkpA)
            комиссии_prop = props.get("Комиссии", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            комиссии_value = 'Тип неизвестен'

            # Свойство: 'Прибыль / Убыток' (Тип: rollup, ID: DM%3Ac)
            прибыль_/_убыток_prop = props.get("Прибыль / Убыток", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            прибыль_/_убыток_value = 'Тип неизвестен'

            # Свойство: 'Оборот открытых Rollup' (Тип: rollup, ID: DomP)
            оборот_открытых_rollup_prop = props.get("Оборот открытых Rollup", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            оборот_открытых_rollup_value = 'Тип неизвестен'

            # Свойство: 'Текущая' (Тип: rollup, ID: Jl%7D%5D)
            текущая_prop = props.get("Текущая", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            текущая_value = 'Тип неизвестен'

            # Свойство: 'Капитализация, $' (Тип: rollup, ID: Js%7CC)
            капитализация,_$_prop = props.get("Капитализация, $", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            капитализация,_$_value = 'Тип неизвестен'

            # Свойство: 'Текущая прибыль' (Тип: formula, ID: Zp%5Bd)
            текущая_прибыль_prop = props.get("Текущая прибыль", {})
            текущая_прибыль_formula_obj = текущая_прибыль_prop.get("formula", {})
            текущая_прибыль_value = текущая_прибыль_formula_obj.get("number", текущая_прибыль_formula_obj.get("string", текущая_прибыль_formula_obj.get("date", "N/A")))

            # Свойство: 'Cделки +' (Тип: formula, ID: %5Be%3E%3C)
            cделки_+_prop = props.get("Cделки +", {})
            cделки_+_formula_obj = cделки_+_prop.get("formula", {})
            cделки_+_value = cделки_+_formula_obj.get("number", cделки_+_formula_obj.get("string", cделки_+_formula_obj.get("date", "N/A")))

            # Свойство: 'Текущий курс' (Тип: rollup, ID: %5BlCP)
            текущий_курс_prop = props.get("Текущий курс", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            текущий_курс_value = 'Тип неизвестен'

            # Свойство: 'Формула прибыли' (Тип: formula, ID: cs%60X)
            формула_прибыли_prop = props.get("Формула прибыли", {})
            формула_прибыли_formula_obj = формула_прибыли_prop.get("formula", {})
            формула_прибыли_value = формула_прибыли_formula_obj.get("number", формула_прибыли_formula_obj.get("string", формула_прибыли_formula_obj.get("date", "N/A")))

            # Свойство: 'Чистая прибыль Rollup' (Тип: rollup, ID: e%3B%3Fy)
            чистая_прибыль_rollup_prop = props.get("Чистая прибыль Rollup", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            чистая_прибыль_rollup_value = 'Тип неизвестен'

            # Свойство: 'Доходность, %' (Тип: formula, ID: fy%3F%5E)
            доходность,_%_prop = props.get("Доходность, %", {})
            доходность,_%_formula_obj = доходность,_%_prop.get("formula", {})
            доходность,_%_value = доходность,_%_formula_obj.get("number", доходность,_%_formula_obj.get("string", доходность,_%_formula_obj.get("date", "N/A")))

            # Свойство: 'Оборот закрытых Rollup' (Тип: rollup, ID: kBOl)
            оборот_закрытых_rollup_prop = props.get("Оборот закрытых Rollup", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            оборот_закрытых_rollup_value = 'Тип неизвестен'

            # Свойство: 'Чистая прибыль' (Тип: formula, ID: kBU%60)
            чистая_прибыль_prop = props.get("Чистая прибыль", {})
            чистая_прибыль_formula_obj = чистая_прибыль_prop.get("formula", {})
            чистая_прибыль_value = чистая_прибыль_formula_obj.get("number", чистая_прибыль_formula_obj.get("string", чистая_прибыль_formula_obj.get("date", "N/A")))

            # Свойство: 'Date' (Тип: date, ID: laaW)
            date_prop = props.get("Date", {})
            date_date_obj = date_prop.get("date", {})
            date_value = date_date_obj.get("start", "N/A") if date_date_obj else "N/A"

            # Свойство: 'Ср. срок Rollup' (Тип: rollup, ID: luu%7B)
            ср._срок_rollup_prop = props.get("Ср. срок Rollup", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            ср._срок_rollup_value = 'Тип неизвестен'

            # Свойство: 'Криптосчет' (Тип: relation, ID: o%3CpV)
            криптосчет_prop = props.get("Криптосчет", {})
            # Тип 'relation' неизвестен. Проверьте документацию Notion API.
            криптосчет_value = 'Тип неизвестен'

            # Свойство: 'Активных' (Тип: rollup, ID: qOe%40)
            активных_prop = props.get("Активных", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            активных_value = 'Тип неизвестен'

            # Свойство: 'Оборот' (Тип: formula, ID: u%40A%3E)
            оборот_prop = props.get("Оборот", {})
            оборот_formula_obj = оборот_prop.get("formula", {})
            оборот_value = оборот_formula_obj.get("number", оборот_formula_obj.get("string", оборот_formula_obj.get("date", "N/A")))

            # Свойство: 'Оборотные, $' (Тип: formula, ID: yIzH)
            оборотные,_$_prop = props.get("Оборотные, $", {})
            оборотные,_$_formula_obj = оборотные,_$_prop.get("formula", {})
            оборотные,_$_value = оборотные,_$_formula_obj.get("number", оборотные,_$_formula_obj.get("string", оборотные,_$_formula_obj.get("date", "N/A")))

            # Свойство: 'Ср. срок' (Тип: formula, ID: zAfo)
            ср._срок_prop = props.get("Ср. срок", {})
            ср._срок_formula_obj = ср._срок_prop.get("formula", {})
            ср._срок_value = ср._срок_formula_obj.get("number", ср._срок_formula_obj.get("string", ср._срок_formula_obj.get("date", "N/A")))

            # Свойство: 'Средний курс' (Тип: formula, ID: %7DwU%5E)
            средний_курс_prop = props.get("Средний курс", {})
            средний_курс_formula_obj = средний_курс_prop.get("formula", {})
            средний_курс_value = средний_курс_formula_obj.get("number", средний_курс_formula_obj.get("string", средний_курс_formula_obj.get("date", "N/A")))

            # Свойство: 'Оборот, мон.' (Тип: rollup, ID: ~%3Dk%5B)
            оборот,_мон._prop = props.get("Оборот, мон.", {})
            # Тип 'rollup' неизвестен. Проверьте документацию Notion API.
            оборот,_мон._value = 'Тип неизвестен'

            # Свойство: '' (Тип: title, ID: title) - Пустое имя, предположим это заголовок
            # ВНИМАНИЕ: Пустое имя свойства может вызвать проблемы. Лучше дать ему имя в Notion.
            # Для примера, если это заголовок, и вы его назовете "Name", используйте:
            # name_prop = props.get("Name", {})
            # name_title_array = name_prop.get("title", [])
            # name_value = name_title_array[0].get("text", {}).get("content", "N/A") if name_title_array else "N/A"
            # Пока оставим как есть, но рекомендуется исправить в Notion.
            _prop = props.get("", {})
            _title_array = _prop.get("title", [])
            name_value = _title_array[0].get("text", {}).get("content", "N/A (Без имени)") if _title_array else "N/A (Без имени)"


            # --- Сбор данных в словарь ---
            # Здесь вы можете выбрать, какие именно свойства использовать в отчетах.
            # Я выбрал несколько, соответствующие вашим требованиям.
            parsed_data.append({
                "page_id": page_id,
                "name": name_value, # Используем значение заголовка (или "N/A (Без имени)")
                "current_profit": текущая_прибыль_value,
                "capitalization": капитализация,_$_value, # Rollup
                "turnover": оборот_value, # Formula
                "deposit_pct": депозит,_%_value, # Formula
                "avg_price": средний_курс_value, # Formula
                "current_price": текущий_курс_value, # Rollup
                # Можно добавить и другие, если понадобятся
                # "other_prop": other_value,
            })

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
    """Формирует строку быстрого отчета."""
    if not 
        return "❌ Не удалось получить данные для отчета."
    report_lines = ["📈 Быстрый отчет по криптосчетам:\n"]
    total_profit = 0
    for item in 
        profit = item.get('current_profit', 0)
        # Проверяем, является ли значение числом, прежде чем складывать
        if profit is not None and isinstance(profit, (int, float)):
             total_profit += profit
        report_lines.append(f"- {item.get('name', 'N/A')}: {'{:.2f}'.format(profit) if profit is not None else 'N/A'}")
    report_lines.append(f"\n💰 Сумма текущей прибыли/убытка: {'{:.2f}'.format(total_profit)}")
    return "\n".join(report_lines)

def format_wide_report(data):
    """Формирует строку широкого отчета."""
    if not 
        return "❌ Не удалось получить данные для отчета."
    report_lines = ["📊 Широкий отчет по криптосчетам:\n"]
    for item in 
        name = item.get('name', 'N/A')
        profit = item.get('current_profit', 'N/A')
        cap = item.get('capitalization', 'N/A')
        turnover = item.get('turnover', 'N/A')
        deposit_pct = item.get('deposit_pct', 'N/A')
        avg_price = item.get('avg_price', 'N/A')
        current_price = item.get('current_price', 'N/A')

        report_lines.append(
            f"🔹 {name}\n"
            f"   - Прибыль/Убыток: {'{:.2f}'.format(profit) if isinstance(profit, (int, float)) else profit}\n"
            f"   - Капитализация: {cap}\n"
            f"   - Оборот: {turnover}\n"
            f"   - Депозит %: {deposit_pct}\n"
            f"   - Средний курс: {avg_price}\n"
            f"   - Текущий курс: {current_price}\n"
        )
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
    if request.method == 'GET':
        return jsonify({"status": "ok"})

    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.info(f"Received webhook  {data}")

            user_id = None
            message_text = None
            sender_name = data.get('sender', {}).get('name', 'Unknown')

            if data.get('event') == 'message':
                user_id = data['sender']['id']
                if data['message']['type'] == 'text':
                    message_text = data['message']['text'].lower()
                else:
                    return jsonify({"status": 0})

            elif data.get('event') == 'conversation_started':
                user_id = data['user']['id']

            if not user_id:
                logger.warning("No user_id found in webhook data.")
                return jsonify({"status": 0})

            if not is_authorized_user(user_id):
                logger.info(f"⛔ Unauthorized access attempt from: {user_id}")
                send_message_with_keyboard(user_id, "❌ Доступ запрещен. Этот бот приватный.")
                return jsonify({"status": 0})

            action_body = data.get('message', {}).get('text')
            if action_body:
                 if action_body == "crypto_menu":
                     send_message_with_keyboard(user_id, "Выберите действие в Крипто:", get_crypto_menu_keyboard())
                 elif action_body == "help_info":
                     send_message_with_keyboard(user_id, "🤖 Это приватный бот.\nИспользуйте меню для навигации.")
                 elif action_body == "back_to_main":
                     send_message_with_keyboard(user_id, "Возврат в главное меню.", get_main_menu_keyboard())
                 elif action_body == "quick_report":
                     crypto_data, error = get_crypto_data_from_notion_http()
                     if error:
                         send_message_with_keyboard(user_id, error)
                     else:
                         report = format_quick_report(crypto_data)
                         send_message_with_keyboard(user_id, report, get_crypto_menu_keyboard())
                 elif action_body == "wide_report":
                     crypto_data, error = get_crypto_data_from_notion_http()
                     if error:
                         send_message_with_keyboard(user_id, error)
                     else:
                         report = format_wide_report(crypto_data)
                         send_message_with_keyboard(user_id, report, get_crypto_menu_keyboard())
                 else:
                     pass

            return jsonify({"status": 0})

        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            return jsonify({"status": 1})

def send_message(user_id, text): # Оставлена для совместимости
    send_message_with_keyboard(user_id, text)

if __name__ == '__main__':
    print(f"🚀 Starting on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=False)
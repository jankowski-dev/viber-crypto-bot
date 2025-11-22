# notion_client.py

import requests
import logging
import os
import math

logger = logging.getLogger(__name__)

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
NOTION_API_VERSION = "2022-06-28"

if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    logger.error("❌ Ошибка: Не заданы учетные данные для Notion (NOTION_TOKEN или NOTION_DATABASE_ID).")
    raise EnvironmentError("Missing Notion credentials.")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_API_VERSION
}

# --- ВАЖНО: Замените 'Название Свойства' на точные названия из вашей БД Notion ---
# Примеры: "Name", "Current Profit", "Текущая прибыль", "Капитализация"
PROPERTY_NAME = "Name"  # Замените на имя свойства с названием счета
PROPERTY_CURRENT_PROFIT = "Current Profit"  # Замените на имя свойства с прибылью/убытком
PROPERTY_CAPITALIZATION = "Capitalization"  # Замените на имя свойства с капитализацией
PROPERTY_TURNOVER = "Turnover"  # Замените на имя свойства с оборотными
PROPERTY_DEPOSIT_PCT = "Deposit %"  # Замените на имя свойства с депозитом %
PROPERTY_AVG_RATE = "Avg Rate"  # Замените на имя свойства со средним курсом
PROPERTY_CURRENT_RATE = "Current Rate"  # Замените на имя свойства с текущим курсом
# --- /ВАЖНО ---


def fetch_all_pages_from_database(query_filter=None):
    """
    Извлекает все страницы из базы данных Notion с использованием пагинации.
    query_filter (опционально): Словарь с фильтром для API запроса.
    Возвращает список всех страниц или None в случае ошибки.
    """
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    pages = []
    has_more = True
    start_cursor = None

    payload = {
        "page_size": 100  # Максимум за один запрос
    }
    if query_filter:
        payload["filter"] = query_filter

    while has_more:
        if start_cursor:
            payload["start_cursor"] = start_cursor

        try:
            logger.info(f"Запрос к Notion API, начиная с cursor: {start_cursor}")
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            result_pages = data.get("results", [])
            pages.extend(result_pages)

            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor", None)

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP ошибка при запросе к Notion: {http_err}")
            logger.error(f"Текст ответа: {response.text}")
            return None
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Ошибка запроса к Notion: {req_err}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при извлечении данных из Notion: {e}")
            return None

    logger.info(f"Получено {len(pages)} страниц из Notion.")
    return pages


def parse_notion_pages(pages):
    """
    Парсит список страниц Notion и извлекает нужные свойства.
    Возвращает список словарей с краткой информацией.
    """
    parsed_data = []
    for page in pages:
        page_id = page.get("id")
        properties = page.get("properties", {})

        # --- Парсинг свойств ---
        # Пример для "Текущая прибыль", предполагаем, что это Formula или Number
        current_profit_raw = properties.get(PROPERTY_CURRENT_PROFIT, {})
        # Обработка разных типов значений в Notion
        current_profit_value = current_profit_raw.get("formula", {}).get("number") \
            if current_profit_raw.get("type") == "formula" \
            else current_profit_raw.get("number") \
            if current_profit_raw.get("type") == "number" \
            else current_profit_raw.get("rich_text", [{}])[0].get("text", {}).get("content") \
            if current_profit_raw.get("type") == "rich_text" \
            else current_profit_raw.get("title", [{}])[0].get("text", {}).get("content") \
            if current_profit_raw.get("type") == "title" \
            else "N/A (Тип неизвестен)"  # Значение по умолчанию

        # --- Повторите для других свойств ---
        name_value = properties.get(PROPERTY_NAME, {}).get("title", [{}])[0].get("text", {}).get("content", "Без названия")
        capitalization_value = properties.get(PROPERTY_CAPITALIZATION, {}).get("number")
        turnover_value = properties.get(PROPERTY_TURNOVER, {}).get("number")
        deposit_pct_value = properties.get(PROPERTY_DEPOSIT_PCT, {}).get("number")
        avg_rate_value = properties.get(PROPERTY_AVG_RATE, {}).get("number")
        current_rate_value = properties.get(PROPERTY_CURRENT_RATE, {}).get("number")

        # --- Формирование словаря ---
        item = {
            "id": page_id,
            "name": name_value,
            "current_profit_raw": current_profit_value,
            "capitalization": capitalization_value,
            "turnover": turnover_value,
            "deposit_pct": deposit_pct_value,
            "avg_rate": avg_rate_value,
            "current_rate": current_rate_value,
        }
        parsed_data.append(item)

    logger.info(f"Парсинг завершен, обработано {len(parsed_data)} элементов.")
    return parsed_data


def analyze_crypto_data(data_list):
    """
    Анализирует список данных криптосчетов.
    Возвращает отфильтрованный список и общую сумму прибыли/убытка.
    """
    # Фильтрация: исключаем нули, '0', '0.0', None, NaN и "N/A (Тип неизвестен)"
    non_zero_items = []
    total_profit = 0.0

    for item in data_list:
        raw_val = item.get("current_profit_raw")

        # Проверяем на "N/A (Тип неизвестен)"
        if raw_val == "N/A (Тип неизвестен)":
            continue  # Пропускаем

        # Пытаемся привести к float
        try:
            profit_float = float(raw_val)
            # Проверяем на NaN
            if math.isnan(profit_float):
                continue  # Пропускаем
            # Проверяем на 0
            if profit_float == 0:
                continue  # Пропускаем
            # Если всё ок, добавляем в список и к сумме
            non_zero_items.append(item)
            total_profit += profit_float
        except (ValueError, TypeError):
            # Если привести к float не удалось, игнорируем (например, если там строка "abc")
            logger.debug(f"Пропущено значение прибыли '{raw_val}' для счета '{item.get('name')}' - не число.")
            continue

    logger.info(f"Фильтрация завершена. Найдено {len(non_zero_items)} счетов с ненулевой прибылью/убытком.")
    return non_zero_items, total_profit


def get_quick_report():
    """
    Получает данные из Notion и возвращает краткий отчет о прибыли/убытке.
    """
    logger.info("Запуск получения быстрого отчета...")
    pages = fetch_all_pages_from_database()
    if pages is None:
        return "❌ Ошибка при извлечении данных из Notion."

    parsed_data = parse_notion_pages(pages)
    if not parsed_data:
        return "⚠️ Данные в базе Notion отсутствуют или не удалось их обработать."

    non_zero_items, total_profit = analyze_crypto_data(parsed_data)

    if not non_zero_items:
        return "📉 Нет криптосчетов с ненулевой прибылью/убытком для отчета."

    # Формируем строку результата
    report_text = f"📈 Краткий отчет:\n"
    report_text += f"Сумма текущей прибыли/убытка: {total_profit:.2f}\n"
    # (Опционально) Добавить количество счетов
    report_text += f"(В расчете участвовало {len(non_zero_items)} счетов)"

    logger.info("Быстрый отчет сформирован.")
    return report_text


def get_wide_report():
    """
    Получает данные из Notion и возвращает подробный отчет о криптосчетах.
    """
    logger.info("Запуск получения широкого отчета...")
    pages = fetch_all_pages_from_database()
    if pages is None:
        return "❌ Ошибка при извлечении данных из Notion."

    parsed_data = parse_notion_pages(pages)
    if not parsed_data:
        return "⚠️ Данные в базе Notion отсутствуют или не удалось их обработать."

    report_text = "📋 Подробный отчет о криптосчетах:\n\n"
    for item in parsed_data:  # Показываем ВСЕ счета
        report_text += f"- Название: {item.get('name', 'N/A')}\n"
        report_text += f"  Прибыль/убыток: {item.get('current_profit_raw', 'N/A')}\n"
        report_text += f"  Капитализация: {item.get('capitalization', 'N/A')}\n"
        report_text += f"  Оборотные: {item.get('turnover', 'N/A')}\n"
        report_text += f"  Депозит %: {item.get('deposit_pct', 'N/A')}\n"
        report_text += f"  Средний курс: {item.get('avg_rate', 'N/A')}\n"
        report_text += f"  Текущий курс: {item.get('current_rate', 'N/A')}\n"
        report_text += "---\n"

    logger.info("Широкий отчет сформирован.")
    return report_text


def check_notion_connection():
    """
    Проверяет подключение к базе данных Notion, извлекая ограниченное количество страниц.
    Возвращает (успешно ли, сообщение об ошибке или успехе).
    """
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logger.error("Notion credentials (NOTION_TOKEN or NOTION_DATABASE_ID) not set.")
        return False, "❌ Ошибка: Не заданы учетные данные для Notion (токен или ID базы данных)."

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    # Запрашиваем только 1 страницу для проверки
    payload = {"page_size": 1}

    try:
        logger.info("Проверка подключения к Notion DB...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Подключение к Notion DB успешно.")
        return True, "✅ Подключение к базе данных Notion успешно!"
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP ошибка при проверке подключения: {http_err}")
        logger.error(f"Текст ответа: {response.text}")
        status_code = response.status_code
        if status_code == 400:
            return False, f"❌ Ошибка 400: Некорректный запрос к базе данных Notion. Проверьте ID базы данных и права интеграции."
        elif status_code == 401:
            return False, f"❌ Ошибка 401: Не авторизован. Проверьте токен интеграции Notion."
        elif status_code == 403:
            return False, f"❌ Ошибка 403: Доступ запрещен. Проверьте права интеграции и доступ к базе данных."
        elif status_code == 404:
            return False, f"❌ Ошибка 404: База данных Notion не найдена. Проверьте ID базы данных."
        else:
            return False, f"❌ Ошибка HTTP при подключении к Notion: {http_err}"
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Ошибка запроса при проверке подключения: {req_err}")
        return False, f"❌ Ошибка запроса к Notion: {req_err}"
    except Exception as e:
        logger.error(f"Неизвестная ошибка при проверке подключения: {e}")
        return False, f"❌ Неизвестная ошибка при подключении к Notion: {e}"

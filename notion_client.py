# notion_client.py

import requests
import logging
import os
# math не нужен без фильтрации
# import math

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

# --- ВАЖНО: Используем названия свойств из файла notion_properties_mapping.txt ---
PROPERTY_CRYPTO_ACCOUNT = "Криптосчет"  # relation
PROPERTY_CURRENT_PROFIT = "Текущая прибыль"  # formula
PROPERTY_CAPITALIZATION = "Капитализация, $"  # rollup
PROPERTY_DEPOSIT_PCT = "Депозит, %"  # formula
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
    Возвращает список словарей с информацией.
    """
    parsed_data = []
    for page in pages:
        page_id = page.get("id")
        properties = page.get("properties", {})

        # --- Парсинг нужных свойств ---
        # Криптосчет (relation)
        crypto_account_raw = properties.get(PROPERTY_CRYPTO_ACCOUNT, {})
        crypto_account_relations = crypto_account_raw.get("relation", [])
        crypto_account_value = crypto_account_relations[0].get("name", "N/A (Тип неизвестен)") if crypto_account_relations else "Нет связи"

        # Текущая прибыль (formula)
        current_profit_raw = properties.get(PROPERTY_CURRENT_PROFIT, {})
        current_profit_formula_obj = current_profit_raw.get("formula", {})
        current_profit_value = current_profit_formula_obj.get("number", current_profit_formula_obj.get("string", current_profit_formula_obj.get("date", "N/A (Тип неизвестен)")))

        # Капитализация, $ (rollup)
        capitalization_raw = properties.get(PROPERTY_CAPITALIZATION, {})
        capitalization_value = capitalization_raw.get("rollup", {}).get("number") \
            if capitalization_raw.get("type") == "rollup" \
            else "N/A (Тип неизвестен)"

        # Депозит, % (formula)
        deposit_pct_raw = properties.get(PROPERTY_DEPOSIT_PCT, {})
        deposit_pct_formula_obj = deposit_pct_raw.get("formula", {})
        deposit_pct_value = deposit_pct_formula_obj.get("number", deposit_pct_formula_obj.get("string", deposit_pct_formula_obj.get("date", "N/A (Тип неизвестен)")))

        # --- Формирование словаря ---
        item = {
            "id": page_id,
            "crypto_account": crypto_account_value,
            "current_profit_raw": current_profit_value,
            "capitalization": capitalization_value,
            "deposit_pct": deposit_pct_value,
        }
        parsed_data.append(item)

    logger.info(f"Парсинг завершен, обработано {len(parsed_data)} элементов.")
    return parsed_data


# Функция analyze_crypto_data больше не нужна без фильтрации


def get_quick_report():
    """
    Получает данные из Notion и возвращает краткий отчет (только указанные колонки).
    """
    logger.info("Запуск получения быстрого отчета (только указанные колонки)...")
    pages = fetch_all_pages_from_database()
    if pages is None:
        return "❌ Ошибка при извлечении данных из Notion."

    parsed_data = parse_notion_pages(pages)
    if not parsed_data: # <-- ИСПРАВЛЕНО: добавлено 'data'
        return "⚠️ Данные в базе Notion отсутствуют или не удалось их обработать."

    # Формируем строку результата
    report_text = f"📈 Краткий отчет (Криптосчет - Прибыль - Капитализация - Депозит %):\n\n"
    for item in parsed_data: # <-- ИСПРАВЛЕНО: добавлено 'data'
        report_text += f"- {item['crypto_account']} - {item['current_profit_raw']} - {item['capitalization']} - {item['deposit_pct']}\n"

    logger.info("Быстрый отчет (указанные колонки) сформирован.")
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
    if not parsed_data: # <-- ИСПРАВЛЕНО: добавлено 'data'
        return "⚠️ Данные в базе Notion отсутствуют или не удалось их обработать."

    report_text = "📋 Подробный отчет о криптосчетах:\n\n"
    for item in parsed_data:  # Показываем ВСЕ счета, ИСПРАВЛЕНО: добавлено 'data'
        report_text += f"- Криптосчет: {item.get('crypto_account', 'N/A')}\n"
        report_text += f"  Прибыль/убыток: {item.get('current_profit_raw', 'N/A')}\n"
        report_text += f"  Капитализация: {item.get('capitalization', 'N/A')}\n"
        report_text += f"  Депозит %: {item.get('deposit_pct', 'N/A')}\n"
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

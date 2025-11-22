# notion_client.py

import requests
import logging
import os

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

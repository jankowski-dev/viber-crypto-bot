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
            # --- ДОБАВЛЕНО: Отладочное логирование ---
            current_profit_raw_prop = props.get("Текущая", {}) # Используем более понятное имя переменной
            logger.debug(f"Raw 'Текущая' property for page {page_id}: {current_profit_raw_prop}") # <-- Логируем исходное значение

            # Для rollup типа number, строка или date, извлекаем соответствующее значение
            # Обычно rollup number возвращает словарь с ключом 'number'
            # Если current_profit_raw_prop сам по себе словарь с ключом 'number', 'string', 'date', нужно проверить это
            current_profit_raw_value = "N/A" # Значение по умолчанию
            if isinstance(current_profit_raw_prop, dict):
                # Проверим структуру ответа для rollup
                # Пример структуры для rollup number: {"type": "number", "number": 123.45}
                # Пример структуры для rollup string: {"type": "string", "string": "some text"}
                rollup_type = current_profit_raw_prop.get("type")
                logger.debug(f"  Rollup type detected: {rollup_type}") # <-- Логируем тип
                if rollup_type == "number":
                    current_profit_raw_value = current_profit_raw_prop.get("number", "N/A")
                elif rollup_type == "string":
                    current_profit_raw_value = current_profit_raw_prop.get("string", "N/A")
                elif rollup_type == "date":
                    # Извлекаем start или end из объекта даты
                    date_obj = current_profit_raw_prop.get("date", {})
                    logger.debug(f"  Date object: {date_obj}") # <-- Логируем объект даты
                    current_profit_raw_value = date_obj.get("start", "N/A") if date_obj else "N/A"
                else:
                    # Если тип не number/string/date, или структура другая
                    # Попробуем получить 'number' или 'string' напрямую, на случай, если 'type' не указан
                    # или структура просто {"number": val} без "type"
                    number_val = current_profit_raw_prop.get("number")
                    string_val = current_profit_raw_prop.get("string")
                    logger.debug(f"  Direct access - number: {number_val}, string: {string_val}") # <-- Логируем прямой доступ
                    if number_val is not None:
                         current_profit_raw_value = number_val
                    elif string_val is not None:
                         current_profit_raw_value = string_val
                    else:
                         # Если ничего не подошло, логируем структуру и используем строку "N/A (Тип неизвестен, struct: ...)"
                         current_profit_raw_value = f"N/A (Тип неизвестен, struct: {list(current_profit_raw_prop.keys())})"
                         logger.debug(f"  Fallback used for 'Текущая', keys were: {list(current_profit_raw_prop.keys())}")
            else:
                # Если current_profit_raw_prop не словарь, значит он сам является значением (редкий случай)
                logger.debug(f"  'Текущая' prop is not a dict: {type(current_profit_raw_prop)}, value: {current_profit_raw_prop}") # <-- Логируем тип и значение
                current_profit_raw_value = current_profit_raw_prop

            logger.debug(f"  Final 'current_profit_raw' value: {current_profit_raw_value}") # <-- Логируем итоговое значение

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


            # --- Сбор *всех* данных в словарь ---
            # Эти данные будут отправлены ИИ для анализа
            parsed_data.append({
                "page_id": page_id,
                "name": name_value, # Используем значение заголовка (или "N/A (Без имени)")
                "current_profit_raw": current_profit_raw_value, # <-- Используем значение из 'Текущая' (число, строка, N/A)
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

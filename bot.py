# Внутри цикла for page in pages: в get_raw_crypto_data_from_notion_http
# ...
            # --- ИСПРАВЛЕНО: Извлечение значения из 'Текущая' (Тип: rollup, ID: Jl%7D%5D) ---
            текущая_prop = props.get("Текущая", {})
            logger.debug(f"Raw 'Текущая' property for page {page_id}: {current_prop}") # <-- Добавим логирование

            # Для rollup типа number, строка или date, извлекаем соответствующее значение
            # Обычно rollup number возвращает словарь с ключом 'number'
            # Если current_prop сам по себе словарь с ключом 'number', 'string', 'date', нужно проверить это
            текущая_rollup_obj = "N/A" # Значение по умолчанию
            if isinstance(текущая_prop, dict):
                # Проверим структуру ответа для rollup
                # Пример структуры для rollup number: {"type": "number", "number": 123.45}
                # Пример структуры для rollup string: {"type": "string", "string": "some text"}
                rollup_type = текущая_prop.get("type")
                logger.debug(f"  Rollup type detected: {rollup_type}") # <-- Логируем тип
                if rollup_type == "number":
                    текущая_rollup_obj = текущая_prop.get("number", "N/A")
                elif rollup_type == "string":
                    текущая_rollup_obj = текущая_prop.get("string", "N/A")
                elif rollup_type == "date":
                    # Извлекаем start или end из объекта даты
                    date_obj = текущая_prop.get("date", {})
                    logger.debug(f"  Date object: {date_obj}") # <-- Логируем объект даты
                    текущая_rollup_obj = date_obj.get("start", "N/A") if date_obj else "N/A"
                else:
                    # Если тип не number/string/date, или структура другая
                    # Попробуем получить 'number' или 'string' напрямую, на случай, если 'type' не указан
                    # или структура просто {"number": val} без "type"
                    number_val = текущая_prop.get("number")
                    string_val = текущая_prop.get("string")
                    logger.debug(f"  Direct access - number: {number_val}, string: {string_val}") # <-- Логируем прямой доступ
                    if number_val is not None:
                         текущая_rollup_obj = number_val
                    elif string_val is not None:
                         текущая_rollup_obj = string_val
                    else:
                         текущая_rollup_obj = f"N/A (Тип неизвестен, struct: {list(текущая_prop.keys())})"
            else:
                # Если текущая_prop не словарь, значит он сам является значением (редкий случай)
                logger.debug(f"  'Текущая' prop is not a dict: {type(текущая_prop)}, value: {текущая_prop}") # <-- Логируем тип и значение
                текущая_rollup_obj = текущая_prop

            logger.debug(f"  Final 'current_profit_raw' value: {current_profit_raw}") # <-- Логируем итоговое значение

# ...
            # --- Сбор *всех* данных в словарь ---
            # Эти данные будут отправлены ИИ для анализа
            parsed_data.append({
                "page_id": page_id,
                "name": name_value, # Используем значение заголовка (или "N/A (Без имени)")
                "current_profit_raw": current_profit_raw, # <-- Используем значение из 'Текущая' (число, строка, N/A)
                "capitalization": capitalization_usd_value, # Rollup - строка
                "turnover": turnover_value, # Formula - может быть числом или строкой
                "deposit_pct": deposit_pct_value, # Formula - может быть числом или строкой
                "avg_price": avg_price_value, # Formula - может быть числом или строкой
                "current_price": current_price_rollup_value, # Rollup - строка
                # Можно добавить и другие, если понадобятся
                # "other_prop": other_value,
            })
# ...
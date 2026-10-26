# Сериализация хранилища

`storage.json` содержит все публичные свойства одного заполненного
`storage_manager`: коллекции `ranges`, `groups`, `warehouses`,
`nomenclatures`, `recipes` и признак `is_loaded`.
Имена свойств определяются через рефлексию, вложенные объекты раскрываются
конвертерами. Фабрика только выбирает подходящий конвертер.

Выгрузка содержит 5 единиц измерения, 3 группы, 3 склада, 4 номенклатуры
и 1 составной рецепт. Даты проверяются на тестовых моделях: в текущих
доменных моделях хранилища таких свойств нет.

## Повторная генерация

Выполнить из корня проекта:

```bash
.venv/bin/python -B - <<'PY'
import json
from pathlib import Path

from Src.Logics.convert_factory import convert_factory
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model

storage = storage_manager()
storage.convert(settings_model())
factory = convert_factory()
data = factory.create(storage).convert(storage)
content = json.dumps(data, ensure_ascii=False, indent=4, allow_nan=False)
Path("Docs/Serialization/storage.json").write_text(content + "\n", encoding="utf-8")
PY
```

Идентификаторы создаются моделями, поэтому при повторной генерации изменятся.
Свойства `id` и `unique_code` возвращают один идентификатор и сохраняются оба.

## Открытый вопрос: циклические ссылки

Правило представления циклов пока не менялось: при повторном появлении объекта
в текущей цепочке обхода сохраняется словарь с его `unique_code`. Это относится
к самоссылкам `base_range` базовых единиц измерения.

Преподаватель отклонил такой способ. Он временно сохранён до уточнения
требований; соответствующее замечание к выгрузке остаётся открытым.

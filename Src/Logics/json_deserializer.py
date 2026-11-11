import json
from pathlib import Path

from typing import Any
from Src.Core.exception import arguments_exception
from Src.Dtos.storage_data_dto import storage_data_dto
from Src.Logics.deserializer import deserializer


class json_deserializer:
    """Внешний адаптер: читает JSON и передаёт данные механизму восстановления."""

    def __init__(self, loader: deserializer):
        """Принимает сервис восстановления моделей из разобранных данных."""
        self.__loader = loader

    @staticmethod
    def __invalid_constant(value: str):
        """Отклоняет NaN и Infinity, не входящие в стандарт JSON."""
        raise arguments_exception("json", f"Недопустимое числовое значение {value}!")

    @staticmethod
    def __object(pairs: list) -> dict:
        """Собирает словарь из пар JSON, отклоняя повторяющиеся имена полей."""
        result = {}
        for key, value in pairs:
            if key in result:
                raise arguments_exception("json", f"Повторное поле {key}!")
            result[key] = value
        return result

    def __parse(self, text: str) -> object:
        """Разбирает JSON с проверкой повторных полей и недопустимых числовых констант."""
        return json.loads(text, parse_constant=self.__invalid_constant,
                          object_pairs_hook=self.__object)

    def loads(self, text: str, model_type: Any) -> object:
        """Прочитать одну модель из JSON-строки с явно заданным типом."""
        return self.__loader.deserialize(self.__parse(text), model_type)

    def loads_storage(self, text: str) -> storage_data_dto:
        """Восстанавливает коллекции моделей хранилища из JSON-строки."""
        return self.__loader.deserialize_storage(self.__parse(text))

    def load_storage(self, file_name: str | Path) -> storage_data_dto:
        """Прочитать UTF-8 файл в формате Docs/Serialization/storage.json."""
        return self.loads_storage(Path(file_name).read_text(encoding="utf-8"))

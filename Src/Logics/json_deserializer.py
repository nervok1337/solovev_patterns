import json
from pathlib import Path

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Dtos.storage_data_dto import storage_data_dto
from Src.Logics.deserializer import deserializer


class json_deserializer:
    """Внешний адаптер: читает JSON и передаёт данные механизму восстановления."""

    def __init__(self, loader: deserializer):
        self.__loader = loader

    @staticmethod
    def __invalid_constant(value: str):
        raise arguments_exception("json", f"Недопустимое числовое значение {value}!")

    @staticmethod
    def __object(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise arguments_exception("json", f"Повторное поле {key}!")
            result[key] = value
        return result

    def __parse(self, text: str) -> dict:
        return json.loads(text, parse_constant=self.__invalid_constant,
                          object_pairs_hook=self.__object)

    def loads(self, text: str, model_type: type[entity_model]) -> entity_model:
        """Прочитать одну модель из JSON-строки с явно заданным типом."""
        return self.__loader.deserialize(self.__parse(text), model_type)

    def loads_storage(self, text: str) -> storage_data_dto:
        return self.__loader.deserialize_storage(self.__parse(text))

    def load_storage(self, file_name: str | Path) -> storage_data_dto:
        """Прочитать UTF-8 файл в формате Docs/Serialization/storage.json."""
        return self.loads_storage(Path(file_name).read_text(encoding="utf-8"))

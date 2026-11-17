import json

from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import argument_exception, validator
from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.deserializer import deserializer
from Src.Models.settings_model import settings_model


class settings_manager(abstract_manager):
    """Преобразует настройки и предоставляет единый экземпляр менеджера."""

    def __new__(cls):
        """Возвращает единственный экземпляр менеджера настроек."""
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        """Инициализирует состояние только при первом создании singleton."""
        if getattr(self, "_settings_manager__initialized", False):
            return

        self.__settings = settings_model()
        self.__is_loaded = False
        self.__initialized = True

    @property
    def is_loaded(self) -> bool:
        """Возвращает признак успешного преобразования настроек."""
        return self.__is_loaded

    def load(self, file_name: str = "settings.json") -> bool:
        """Загружает настройки из JSON-файла и преобразует их в модель."""
        validator.validate(file_name, str)

        with open(file_name, encoding="utf-8") as file:
            data = json.load(file)

        return self.convert(data)

    def convert(self, data: dict) -> bool:
        """Восстанавливает настройки общей десериализацией, сохраняя прежний контракт."""
        validator.validate(data, dict)
        for field in ("organization", "account_name", "is_first_start", "response_format"):
            if field not in data:
                raise argument_exception(f"Не указана настройка: {field}")
        values = data.copy()
        validator.validate(values["response_format"], str)
        try:
            values["response_format"] = report_type_enum[values["response_format"].strip().upper()].value
            if not values.get("boss_name"):
                values.pop("boss_name", None)
            converted_settings = deserializer(deserialize_factory()).deserialize(values, settings_model)
        except (KeyError, ValueError) as error:
            raise argument_exception(str(error)) from error
        self.__settings = converted_settings
        self.__is_loaded = True
        return True

    @property
    def settings(self) -> settings_model:
        """Возвращает преобразованные настройки приложения."""
        return self.__settings

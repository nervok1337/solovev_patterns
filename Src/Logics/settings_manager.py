from collections.abc import Callable

from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import argument_exception, validator
from Src.Models.settings_model import settings_model


class settings_manager(abstract_manager):
    """Преобразует настройки и предоставляет единый экземпляр менеджера."""

    def __new__(cls, restore: Callable, load: Callable):
        """Возвращает единственный экземпляр менеджера настроек."""
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, restore: Callable, load: Callable) -> None:
        """Инициализирует состояние только при первом создании singleton."""
        if getattr(self, "_settings_manager__initialized", False):
            return

        self.__restore = restore
        self.__load = load
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

        try:
            return self.__accept(self.__load(file_name, settings_model))
        except ValueError as error:
            raise argument_exception(str(error)) from error

    def convert(self, data: dict) -> bool:
        """Передаёт восстановление модели общему внедрённому механизму."""
        validator.validate(data, dict)
        try:
            return self.__accept(self.__restore(data, settings_model))
        except ValueError as error:
            raise argument_exception(str(error)) from error

    def __accept(self, candidate: settings_model) -> bool:
        """Заменяет настройки только после успешного восстановления и проверки."""
        candidate.validate()
        self.__settings = candidate
        self.__is_loaded = True
        return True

    @property
    def settings(self) -> settings_model:
        """Возвращает преобразованные настройки приложения."""
        return self.__settings

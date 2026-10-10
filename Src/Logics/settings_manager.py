from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import validator
from Src.Models.organization_model import organization_model
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

    def convert(self, data: dict) -> bool:
        """Проверяет словарь и преобразует его в модель настроек."""
        validator.validate(data, dict)

        organization_data = data.get("organization")
        boss_name = data.get("boss_name", "")
        account_name = data.get("account_name")
        is_first_start = data.get("is_first_start")

        validator.validate(organization_data, dict)
        validator.validate(organization_data.get("name"), str, 50)
        validator.validate(organization_data.get("inn"), str)
        validator.validate(organization_data.get("bik"), str)
        validator.validate(organization_data.get("account"), str)
        validator.validate(organization_data.get("ownership_form"), str)
        if boss_name:
            validator.validate(boss_name, str, 255)
        validator.validate(account_name, str, 255)
        validator.validate(is_first_start, bool)

        organization = organization_model(
            organization_data["name"],
            organization_data["inn"],
            organization_data["bik"],
            organization_data["account"],
            organization_data["ownership_form"],
        )
        converted_settings = settings_model()
        converted_settings.organization = organization
        if boss_name:
            converted_settings.boss_name = boss_name
        converted_settings.account_name = account_name
        converted_settings.is_first_start = is_first_start

        self.__settings = converted_settings
        self.__is_loaded = True
        return True

    @property
    def settings(self) -> settings_model:
        """Возвращает преобразованные настройки приложения."""
        return self.__settings

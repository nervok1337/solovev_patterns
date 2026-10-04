import pytest

from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import argument_exception
from Src.Logics.settings_manager import settings_manager


@pytest.fixture(autouse=True)
def reset_settings_manager_singleton():
    """Изолирует состояние singleton между модульными тестами."""
    if hasattr(settings_manager, "instance"):
        delattr(settings_manager, "instance")
    yield
    if hasattr(settings_manager, "instance"):
        delattr(settings_manager, "instance")


@pytest.fixture
def settings_data():
    """Возвращает корректные исходные данные для преобразования."""
    return {
        "organization": {
            "name": "ООО Ромашка",
            "inn": "3801000000",
            "bik": "042520607",
            "account": "40702810000000000001",
            "ownership_form": "ООО",
        },
        "boss_name": "Иванов Иван Иванович",
        "account_name": "Петрова Анна Сергеевна",
        "is_first_start": True,
    }


def test_equals_settings_manager_create():
    """Проверяет, что конструктор возвращает один экземпляр менеджера."""
    first_instance = settings_manager()
    second_instance = settings_manager()

    assert first_instance is second_instance


def test_settings_manager_inherits_abstract_manager():
    """Проверяет наследование менеджера настроек от общего менеджера."""
    assert isinstance(settings_manager(), abstract_manager)


def test_is_loaded_settings_manager_false_before_convert():
    """Проверяет начальное состояние менеджера до преобразования."""
    assert not settings_manager().is_loaded


def test_convert_settings_manager_returns_true(settings_data):
    """Проверяет успешный результат преобразования настроек."""
    result = settings_manager().convert(settings_data)

    assert result


def test_convert_settings_manager_maps_all_fields(settings_data):
    """Проверяет перенос всех полей словаря в доменную модель."""
    manager = settings_manager()

    manager.convert(settings_data)

    assert manager.settings.organization.name == "ООО Ромашка"
    assert manager.settings.organization.inn == "3801000000"
    assert manager.settings.organization.bik == "042520607"
    assert manager.settings.organization.account == "40702810000000000001"
    assert manager.settings.organization.ownership_form == "ООО"
    assert manager.settings.boss_name == "Иванов Иван Иванович"
    assert manager.settings.account_name == "Петрова Анна Сергеевна"
    assert manager.settings.is_first_start is True
    assert manager.is_loaded


def test_convert_settings_manager_without_boss_name(settings_data):
    """Проверяет загрузку настроек без необязательного имени директора."""
    settings_data.pop("boss_name")
    manager = settings_manager()

    result = manager.convert(settings_data)

    assert result
    assert manager.settings.boss_name == ""
    assert manager.is_loaded


def test_argument_exception_settings_manager_invalid_data():
    """Проверяет ошибку при неполном наборе исходных данных."""
    with pytest.raises(argument_exception):
        settings_manager().convert({})


def test_second_create_settings_manager_preserves_converted_data(settings_data):
    """Проверяет, что повторный конструктор не сбрасывает singleton."""
    first_instance = settings_manager()
    first_instance.convert(settings_data)
    converted_settings = first_instance.settings

    second_instance = settings_manager()

    assert second_instance.settings is converted_settings
    assert second_instance.is_loaded

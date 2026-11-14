import pytest

from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import argument_exception
from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.settings_manager import settings_manager


def create_manager():
    """Собирает зависимости менеджера в тесте, сохраняя прежние проверки."""
    from Src.Logics.deserializer import deserializer
    from Src.Logics.deserialize_factory import deserialize_factory
    from Src.Logics.json_deserializer import json_deserializer
    restore = deserializer(deserialize_factory())
    return settings_manager(restore.deserialize, json_deserializer(restore).load)


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
        "response_format": "Markdown",
    }


def test_equals_settings_manager_create():
    """Проверяет, что конструктор возвращает один экземпляр менеджера."""
    first_instance = create_manager()
    second_instance = create_manager()

    assert first_instance is second_instance


def test_settings_manager_inherits_abstract_manager():
    """Проверяет наследование менеджера настроек от общего менеджера."""
    assert isinstance(create_manager(), abstract_manager)


def test_is_loaded_settings_manager_false_before_convert():
    """Проверяет начальное состояние менеджера до преобразования."""
    assert not create_manager().is_loaded


def test_convert_settings_manager_returns_true(settings_data):
    """Проверяет успешный результат преобразования настроек."""
    result = create_manager().convert(settings_data)

    assert result


def test_convert_settings_manager_maps_all_fields(settings_data):
    """Проверяет перенос всех полей словаря в доменную модель."""
    manager = create_manager()

    manager.convert(settings_data)

    assert manager.settings.organization.name == "ООО Ромашка"
    assert manager.settings.organization.inn == "3801000000"
    assert manager.settings.organization.bik == "042520607"
    assert manager.settings.organization.account == "40702810000000000001"
    assert manager.settings.organization.ownership_form == "ООО"
    assert manager.settings.boss_name == "Иванов Иван Иванович"
    assert manager.settings.account_name == "Петрова Анна Сергеевна"
    assert manager.settings.is_first_start is True
    assert manager.settings.response_format is report_type_enum.MARKDOWN
    assert manager.is_loaded


def test_not_raise_settings_manager_convert_without_boss_name(settings_data):
    """Проверяет загрузку настроек без необязательного имени директора."""
    settings_data.pop("boss_name")
    manager = create_manager()

    result = manager.convert(settings_data)

    assert result
    assert manager.settings.boss_name == ""
    assert manager.is_loaded


def test_argument_exception_settings_manager_invalid_data():
    """Проверяет ошибку при неполном наборе исходных данных."""
    with pytest.raises(argument_exception):
        create_manager().convert({})


def test_second_create_settings_manager_preserves_converted_data(settings_data):
    """Проверяет, что повторный конструктор не сбрасывает singleton."""
    first_instance = create_manager()
    first_instance.convert(settings_data)
    converted_settings = first_instance.settings

    second_instance = create_manager()

    assert second_instance.settings is converted_settings
    assert second_instance.is_loaded


def test_load_settings_manager_reads_json_file(tmp_path, settings_data):
    """Проверяет загрузку и преобразование настроек из JSON-файла."""
    import json

    file_name = tmp_path / "settings.json"
    file_name.write_text(json.dumps(settings_data), encoding="utf-8")
    manager = create_manager()

    result = manager.load(str(file_name))

    assert result is True
    assert manager.is_loaded
    assert manager.settings.response_format is report_type_enum.MARKDOWN


def test_argument_exception_settings_manager_unknown_response_format(settings_data):
    """Проверяет отклонение неподдерживаемого формата ответа."""
    settings_data["response_format"] = "PDF"

    with pytest.raises(argument_exception):
        create_manager().convert(settings_data)

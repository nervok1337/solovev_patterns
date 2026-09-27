import pytest

from Src.Core.abstract_model import abstract_model
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


class entity_for_test(abstract_model):
    """Тестовая реализация абстрактной модели."""


def test_unique_code_not_empty_after_abstract_model_created():
    """Проверяет создание непустого уникального кода."""
    entity = entity_for_test()

    assert entity.unique_code != ""


def test_unique_code_differs_for_two_abstract_models():
    """Проверяет уникальность кодов двух моделей."""
    first_entity = entity_for_test()
    second_entity = entity_for_test()

    assert first_entity.unique_code != second_entity.unique_code


def test_entities_equal_when_unique_codes_equal():
    """Проверяет равенство моделей с одинаковыми кодами."""
    first_entity = entity_for_test()
    second_entity = entity_for_test()
    first_entity.unique_code = "fff"
    second_entity.unique_code = "fff"

    assert first_entity == second_entity


def test_arguments_exception_raised_when_entity_name_empty():
    """Проверяет ошибку при пустом наименовании сущности."""
    entity = entity_model()

    with pytest.raises(arguments_exception):
        entity.name = ""


def test_arguments_exception_text_correct_when_unique_code_empty():
    """Проверяет текст ошибки при пустом уникальном коде."""
    field = "value"
    message = "Некорректно передан параметр!"
    entity = entity_for_test()

    with pytest.raises(arguments_exception) as exception:
        entity.unique_code = ""

    assert str(exception.value) == (
        f"Ошибка: Некорректный аргумент {field}!\n"
        f"{message}\n"
    )

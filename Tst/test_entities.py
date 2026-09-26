# Необходимо установить pip install pytest в терминале с подключенным Environment
# Далее, настройки
# {
#    "python.testing.pytestArgs": [
#        "Tst"
#    ],
#    "python.testing.unittestEnabled": false,
#    "python.testing.pytestEnabled": true
#}
from Src.Core.abstract_model import abstract_model 
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
import pytest

class test_entity(abstract_model):
    pass


# Пример простого теста
def test_abstract_model_get_id_not_null():
    # Подготовка
    entity = test_entity()

    # Действие
    result = entity.unique_code

    assert result != ""

# Проверка на создание уникального кода 
def test_abstract_model_get_id_unique():
    # Подготовка
    entity_1 = test_entity()
    entity_2 = test_entity()

    # Действие
    id_1 = entity_1.unique_code
    id_2 = entity_2.unique_code

    assert id_1 != id_2

# Проверка на равенство по признаку одинакового уникального кода
def test_abstract_model_equal_id():
    # Подготовка
    entity_1 = test_entity()
    entity_2 = test_entity()

    # Действие
    entity_1.unique_code = "fff"
    entity_2.unique_code = "fff"

    assert entity_1 == entity_2

# Проверка присвоения пустого имени
def test_entity_model_name_not_empty():
    # Подготовка
    entity_1 = entity_model()
    name = ""

    # Действие
    with pytest.raises(ValueError):
        entity_1.name = name

# Проверка класса ошибок
def test_abstract_model_exception():
    # Подготовка
    field = "value"
    message = "Некорректно передан параметр!"

    #Действие
    entity_1 = test_entity()

    with pytest.raises(arguments_exception) as exc:
        entity_1.unique_code = ""

    assert str(exc.value) == (
        f"Ошибка: Некорректный аргумент {field}!\n"
        f"{message}\n"
    )

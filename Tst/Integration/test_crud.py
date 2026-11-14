"""<summary>Проверки пяти пунктов домашнего задания через HTTP.</summary>"""
import importlib
import json

import pytest
import yaml
from starlette.testclient import TestClient

from Src.Core.validator import argument_exception
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager


@pytest.fixture
def client(monkeypatch):
    """Собирает приложение с изолированными экземплярами существующих singleton."""
    monkeypatch.delattr(storage_manager, 'instance', raising=False)
    monkeypatch.delattr(settings_manager, 'instance', raising=False)
    import main
    app = importlib.reload(main)
    with TestClient(app.api) as session:
        yield session


def create(client, collection, data):
    """Создаёт объект HTTP-запросом и проверяет успешный результат."""
    response = client.post(f'/api/entities/{collection}', json=data)
    assert response.status_code == 201, response.text
    return response.json()


def ref(entity):
    """Создаёт представление ссылки на доменный объект."""
    return {'ref': entity['unique_code']}


@pytest.fixture
def inputs(client):
    """Создаёт зависимости для проверки существующих типов моделей."""
    group = create(client, 'groups', {'name': 'Тестовая группа'})
    unit = create(client, 'ranges', {'name': 'Тестовая единица', 'conversion_factor': 1})
    product_data = {'name': 'Товар', 'full_name': 'Тестовый товар', 'group': ref(group), 'range': ref(unit)}
    product = create(client, 'nomenclatures', product_data)
    return {
        'groups': {'name': 'Новая группа'},
        'warehouses': {'name': 'Новый склад'},
        'ranges': {'name': 'Новая единица', 'conversion_factor': 1},
        'organization': {'name': 'Организация', 'inn': '123', 'bik': '456', 'account': '789', 'ownership_form': 'ООО'},
        'nomenclatures': product_data,
        'ingredients': {'nomenclature': ref(product), 'gross_weight': 20, 'net_weight': 15},
        'recipes': {'name': 'Новый рецепт', 'ingredients': []},
    }


@pytest.mark.parametrize('collection', ['groups', 'warehouses', 'ranges', 'organization', 'nomenclatures', 'ingredients', 'recipes'])
def test_success_crud_all_domain_types(client, inputs, collection):
    """<summary>Создаёт, читает, изменяет и удаляет каждый тип доменной сущности.</summary>"""
    # Подготовка
    data = inputs[collection].copy()

    # Действие
    created = create(client, collection, data)
    url = f"/api/entities/{collection}/{created['unique_code']}"
    read = client.get(url)
    listed = client.get(f'/api/entities/{collection}')
    data['name'] = 'Изменённое имя'
    updated = client.put(url, json=data)
    deleted = client.delete(url)

    # Проверки
    assert read.json() == created
    assert created in listed.json()
    assert updated.status_code == 200, updated.text
    assert updated.json()['name'] == 'Изменённое имя'
    assert updated.json()['unique_code'] == created['unique_code']
    assert deleted.status_code == 204
    assert deleted.content == b''
    assert client.get(url).status_code == 404


def test_conflict_delete_or_recode_used_group(client, inputs):
    """<summary>Запрещает удаление и смену кода используемой группы, разрешая обычное изменение.</summary>"""
    # Подготовка
    code = inputs['nomenclatures']['group']['ref']
    url = f'/api/entities/groups/{code}'

    # Действие
    deletion = client.delete(url)
    recoding = client.put(url, json={'name': 'Не сохранять', 'unique_code': 'blocked-code'})
    rename = client.put(url, json={'name': 'Новое имя группы'})

    # Проверки
    assert deletion.status_code == recoding.status_code == 409
    assert rename.status_code == 200
    assert client.get(url).json()['name'] == 'Новое имя группы'
    assert client.get('/api/entities/groups/blocked-code').status_code == 404


def test_success_recode_free_entity_and_rollback_duplicate(client):
    """<summary>Меняет свободный код и откатывает всё изменение при занятом коде.</summary>"""
    # Подготовка
    first = create(client, 'groups', {'name': 'Первая', 'unique_code': 'first'})
    create(client, 'groups', {'name': 'Вторая', 'unique_code': 'second'})

    # Действие
    rejected = client.put('/api/entities/groups/first', json={'name': 'Не сохранять', 'unique_code': 'second'})
    unchanged = client.get('/api/entities/groups/first')
    changed = client.put('/api/entities/groups/first', json={'name': 'Первая', 'unique_code': 'third'})

    # Проверки
    assert rejected.status_code == 409
    assert unchanged.json() == first
    assert changed.status_code == 200
    assert client.get('/api/entities/groups/first').status_code == 404
    assert client.get('/api/entities/groups/third').json()['unique_code'] == 'third'


def test_success_linked_update_and_atomic_validation(client, inputs):
    """<summary>Обновляет общий ингредиент без потери связей и откатывает неверные веса.</summary>"""
    # Подготовка
    data = inputs['ingredients'].copy()
    ingredient = create(client, 'ingredients', data)
    recipe = create(client, 'recipes', {'name': 'Рецепт', 'ingredients': [ref(ingredient)]})
    url = f"/api/entities/ingredients/{ingredient['unique_code']}"

    # Действие
    bad = client.put(url, json={**data, 'gross_weight': 5, 'net_weight': 10})
    unchanged = client.get(url)
    good = client.put(url, json={**data, 'gross_weight': 10, 'net_weight': 8})
    updated_recipe = client.get(f"/api/entities/recipes/{recipe['unique_code']}")

    # Проверки
    assert bad.status_code == 400
    assert unchanged.json() == ingredient
    assert good.status_code == 200, good.text
    assert updated_recipe.json()['gross_weight'] == 10
    assert updated_recipe.json()['net_weight'] == 8
    assert client.delete(url).status_code == 409


def test_invalid_recipe_cycle_rolls_back(client):
    """<summary>Отклоняет цикл между существующими рецептами без частичного сохранения.</summary>"""
    # Подготовка
    first = create(client, 'recipes', {'name': 'Первый'})
    second = create(client, 'recipes', {'name': 'Второй', 'ingredients': [ref(first)]})
    url = f"/api/entities/recipes/{first['unique_code']}"

    # Действие
    response = client.put(url, json={'name': 'Первый', 'ingredients': [ref(second)]})

    # Проверки
    assert response.status_code == 400
    assert client.get(url).json() == first


def test_invalid_unit_cycle_and_base_coefficient(client):
    """<summary>Проверяет базовую единицу, цикл пересчёта и входящие ссылки производной единицы.</summary>"""
    # Подготовка
    base = create(client, 'ranges', {'name': 'База', 'conversion_factor': 1, 'base_range': None})
    derived = create(client, 'ranges', {'name': 'Производная', 'conversion_factor': 1000, 'base_range': ref(base)})
    url = f"/api/entities/ranges/{base['unique_code']}"

    # Действие
    factor = client.put(url, json={'name': 'База', 'conversion_factor': 2, 'base_range': ref(base)})
    cycle = client.put(url, json={'name': 'База', 'conversion_factor': 1, 'base_range': ref(derived)})

    # Проверки
    assert factor.status_code == cycle.status_code == 400
    assert client.get(url).json() == base
    assert client.delete(url).status_code == 409
    assert client.delete(f"/api/entities/ranges/{derived['unique_code']}").status_code == 204
    assert client.delete(url).status_code == 204


@pytest.mark.parametrize('data', [{'name': ''}, {'name': 12}, {'name': 'X' * 51}, {'name': 'X', 'unknown': 1}, {'name': 'X', 'unique_code': ''}, [], None])
def test_invalid_create_does_not_change_collection(client, data):
    """<summary>Проверяет отклонение неверных полей и отсутствие побочных изменений.</summary>"""
    # Подготовка
    before = client.get('/api/entities/groups').json()

    # Действие
    response = client.post('/api/entities/groups', content=json.dumps(data), headers={'Content-Type': 'application/json'})

    # Проверки
    assert response.status_code == 400
    assert client.get('/api/entities/groups').json() == before


def test_invalid_references_and_unknown_collections(client, inputs):
    """<summary>Отклоняет отсутствующие ссылки, неверные типы и доступ к внутренним атрибутам.</summary>"""
    # Подготовка
    data = inputs['nomenclatures'].copy()

    # Действие и проверки
    for value in [{'ref': 'missing'}, data['range'], {'name': 'Скрытое создание'}]:
        response = client.post('/api/entities/nomenclatures', json={**data, 'group': value})
        assert response.status_code == 400
    for collection in ['unknown', '__dict__', 'is_loaded']:
        assert client.get(f'/api/entities/{collection}').status_code == 400


def test_success_swagger_formats_and_existing_reports(client):
    """<summary>Проверяет Swagger, список зарегистрированных форматов и существующие отчёты после CRUD.</summary>"""
    # Подготовка
    entity = create(client, 'groups', {'name': 'Группа для отчёта'})
    params = {'type': 'groups', 'code': entity['unique_code']}

    # Действие
    formats = client.get('/api/report-formats')
    spec = yaml.safe_load(client.get('/api-spec.yaml').text)

    # Проверки
    assert formats.status_code == 200
    assert formats.json()
    assert client.get('/ui/').status_code == 200
    assert '/api/entities/{entity_type}' in spec['paths']
    assert client.get('/api/get_default_report', params=params).status_code == 200
    for name in formats.json():
        response = client.get('/api/get_report', params={**params, 'format': name})
        assert response.status_code == 200, response.text
        assert response.content


def test_success_settings_use_injected_general_loader(tmp_path):
    """<summary>Проверяет общую десериализацию настроек без чтения файла внутри менеджера.</summary>"""
    # Подготовка
    from Src.Logics.deserialize_factory import deserialize_factory
    from Src.Logics.deserializer import deserializer
    from Src.Logics.json_deserializer import json_deserializer
    from Src.Models.settings_model import settings_model
    if hasattr(settings_manager, 'instance'):
        del settings_manager.instance
    restore = deserializer(deserialize_factory())
    adapter = json_deserializer(restore)
    data = {'organization': {'name': 'ООО', 'inn': '1', 'bik': '2', 'account': '3', 'ownership_form': 'ООО'},
            'account_name': 'Бухгалтер', 'is_first_start': False, 'response_format': 'TXT'}
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    calls = []

    def load(file_name, model_type):
        """Фиксирует вызов внешнего адаптера загрузки."""
        calls.append((file_name, model_type))
        return adapter.load(file_name, model_type)

    manager = settings_manager(restore.deserialize, load)

    # Действие
    manager.load(str(path))
    previous = manager.settings
    path.write_text('{"organization": false}', encoding='utf-8')
    with pytest.raises(argument_exception):
        manager.load(str(path))

    # Проверки
    assert calls[0] == (str(path), settings_model)
    assert manager.settings is previous
    assert manager.settings.organization.name == 'ООО'

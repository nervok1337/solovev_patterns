import importlib
import json

import pytest
import yaml
from starlette.testclient import TestClient

from Src.Core.validator import argument_exception
from Src.Logics.convert_factory import convert_factory
from Src.Logics.deserializer import deserializer
from Src.Logics.json_deserializer import json_deserializer
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager
from Src.Models.settings_model import settings_model


CONFIG = {
    "organization": {"name": "ООО", "inn": "1", "bik": "2", "account": "3", "ownership_form": "ООО"},
    "account_name": "Бухгалтер", "is_first_start": True, "response_format": "TXT",
}


@pytest.fixture
def client(monkeypatch):
    """Собирает настоящий API с независимыми данными без локального settings.json."""
    monkeypatch.delattr(storage_manager, "instance", raising=False)
    monkeypatch.delattr(settings_manager, "instance", raising=False)

    def load(manager, file_name="settings.json"):
        """Загружает тестовую конфигурацию через настоящий общий механизм."""
        return manager.convert(CONFIG)

    monkeypatch.setattr(settings_manager, "load", load)
    import main
    application = importlib.reload(main)
    with TestClient(application.api) as session:
        yield session


def create(client, collection, data):
    """Создаёт объект публичным API и проверяет HTTP 201."""
    response = client.post(f"/api/entities/{collection}", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def ref(entity):
    """Формирует ссылку на существующую доменную сущность."""
    return {"ref": entity["unique_code"]}


@pytest.fixture
def inputs(client):
    """Создаёт связанные исходные данные для CRUD всех доменных типов."""
    group = create(client, "groups", {"name": "Группа"})
    unit = create(client, "ranges", {"name": "Штука", "conversion_factor": 1})
    product_data = {"name": "Товар", "full_name": "Товар", "group": ref(group), "range": ref(unit)}
    product = create(client, "nomenclatures", product_data)
    return {
        "groups": {"name": "Новая группа"},
        "warehouses": {"name": "Новый склад"},
        "ranges": {"name": "Грамм", "conversion_factor": 1},
        "organization": {"name": "Кафе", "inn": "1", "bik": "2", "account": "3", "ownership_form": "ООО"},
        "nomenclatures": product_data,
        "ingredients": {"nomenclature": ref(product), "gross_weight": 20, "net_weight": 15},
        "recipes": {"name": "Рецепт", "ingredients": []},
    }


@pytest.mark.parametrize("collection", ["groups", "warehouses", "ranges", "organization", "nomenclatures", "ingredients", "recipes"])
def test_success_crud_all_domain_types(client, inputs, collection):
    """<summary>Проверяет полный цикл создания, чтения, изменения и удаления каждого типа через HTTP.</summary>"""
    # Подготовка
    data = inputs[collection]

    # Действие
    created = create(client, collection, data)
    url = f"/api/entities/{collection}/{created['unique_code']}"
    read = client.get(url)
    listed = client.get(f"/api/entities/{collection}")
    updated = client.put(url, json={**data, "name": "Новое имя"})
    deleted = client.delete(url)

    # Проверки
    assert read.status_code == listed.status_code == 200
    assert read.json() == created
    assert created in listed.json()
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Новое имя"
    assert updated.json()["unique_code"] == created["unique_code"]
    assert deleted.status_code == 204 and not deleted.content
    assert client.get(url).status_code == 404


def test_success_reference_lifecycle_and_atomic_validation(client, inputs):
    """<summary>Проверяет ссылки в свойствах и списках, обновление зависимостей и освобождение счётчиков.</summary>"""
    # Подготовка
    data = inputs["ingredients"]
    ingredient = create(client, "ingredients", data)
    recipe = create(client, "recipes", {"name": "Рецепт", "ingredients": [ref(ingredient)]})
    ingredient_url = f"/api/entities/ingredients/{ingredient['unique_code']}"
    recipe_url = f"/api/entities/recipes/{recipe['unique_code']}"
    group_code = inputs["nomenclatures"]["group"]["ref"]
    group_url = f"/api/entities/groups/{group_code}"

    # Действие
    blocked_delete = client.delete(ingredient_url)
    blocked_code = client.put(ingredient_url, json={**data, "unique_code": "blocked"})
    blocked_group = client.delete(group_url)
    invalid = client.put(ingredient_url, json={**data, "gross_weight": 5, "net_weight": 10})
    unchanged = client.get(ingredient_url)
    changed = client.put(ingredient_url, json={**data, "gross_weight": 10, "net_weight": 8})
    related = client.get(recipe_url)
    released = client.put(recipe_url, json={"name": "Рецепт", "ingredients": []})
    deleted = client.delete(ingredient_url)

    # Проверки
    assert blocked_delete.status_code == blocked_code.status_code == blocked_group.status_code == 409
    assert invalid.status_code == 400
    assert unchanged.json() == ingredient
    assert changed.status_code == 200
    assert related.json()["gross_weight"] == 10 and related.json()["net_weight"] == 8
    assert released.status_code == 200 and deleted.status_code == 204


def test_success_recode_and_failed_changes_preserve_data(client):
    """<summary>Проверяет свободную смену кода, конфликты и отсутствие частичных изменений при неверных данных.</summary>"""
    # Подготовка
    original = create(client, "groups", {"name": "Первая", "unique_code": "first"})
    create(client, "groups", {"name": "Вторая", "unique_code": "second"})
    url = "/api/entities/groups/first"

    # Действие
    conflict = client.put(url, json={"name": "Не сохранять", "unique_code": "second"})
    unchanged = client.get(url)
    invalid = client.put(url, json={"name": "Не сохранять", "unknown": 1})
    changed = client.put(url, json={"name": "Первая", "unique_code": "third"})

    # Проверки
    assert conflict.status_code == 409
    assert unchanged.json() == original
    assert invalid.status_code == 400
    assert changed.status_code == 200
    assert client.get(url).status_code == 404
    assert client.get("/api/entities/groups/third").json()["name"] == "Первая"
    unit = create(client, "ranges", {"name": "Свободная база", "conversion_factor": 1})
    renamed = client.put(f"/api/entities/ranges/{unit['unique_code']}", json={**unit, "unique_code": "new-base"})
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["base_range"] == {"ref": "new-base"}
    assert client.delete("/api/entities/ranges/new-base").status_code == 204
    for data in ({"name": ""}, {"name": 12}, {"name": "X" * 51}, {"name": "X", "unique_code": ""}, [], None):
        before = client.get("/api/entities/groups").json()
        response = client.post("/api/entities/groups", content=json.dumps(data), headers={"Content-Type": "application/json"})
        assert response.status_code == 400
        assert client.get("/api/entities/groups").json() == before


def test_invalid_links_and_cycles_preserve_graph(client, inputs):
    """<summary>Отклоняет неверные ссылки, циклы рецептов и единиц, сохраняя корректные связи и самоссылку базы.</summary>"""
    # Подготовка
    first = create(client, "recipes", {"name": "Первый"})
    second = create(client, "recipes", {"name": "Второй", "ingredients": [ref(first)]})
    base = create(client, "ranges", {"name": "База", "conversion_factor": 1})
    derived = create(client, "ranges", {"name": "Производная", "conversion_factor": 1000, "base_range": ref(base)})
    recipe_url = f"/api/entities/recipes/{first['unique_code']}"
    base_url = f"/api/entities/ranges/{base['unique_code']}"

    # Действие
    recipe_cycle = client.put(recipe_url, json={"name": "Первый", "ingredients": [ref(second)]})
    unit_cycle = client.put(base_url, json={"name": "База", "conversion_factor": 1, "base_range": ref(derived)})
    invalid_base = client.put(base_url, json={"name": "База", "conversion_factor": 2, "base_range": ref(base)})

    # Проверки
    assert recipe_cycle.status_code == unit_cycle.status_code == invalid_base.status_code == 400
    assert client.get(recipe_url).json() == first
    assert client.get(base_url).json() == base
    assert client.delete(base_url).status_code == 409
    assert client.delete(f"/api/entities/ranges/{derived['unique_code']}").status_code == 204
    assert client.delete(base_url).status_code == 204
    data = inputs["nomenclatures"]
    for link in ({"ref": "missing"}, data["range"], {"name": "Скрытое создание"}):
        assert client.post("/api/entities/nomenclatures", json={**data, "group": link}).status_code == 400
    assert client.get("/api/entities/unknown").status_code == 400


def test_success_legacy_serialization_swagger_and_reports(client):
    """<summary>Проверяет прежнюю выгрузку/загрузку хранилища, Swagger и актуальные отчёты после CRUD.</summary>"""
    # Подготовка
    import main
    factory = convert_factory()
    before = factory.create(main.storage).convert(main.storage)
    entity = create(client, "groups", {"name": "Для отчёта"})
    params = {"type": "groups", "code": entity["unique_code"]}

    # Действие
    formats = client.get("/api/report-formats")
    spec = yaml.safe_load(client.get("/api-spec.yaml").text)
    after = factory.create(main.storage).convert(main.storage)
    loader = json_deserializer(deserializer(deserialize_factory()))
    restored = loader.loads_storage(json.dumps(after))

    # Проверки
    assert before == after
    assert factory.create(restored).convert(restored) == before
    assert set(after) == {"ranges", "groups", "warehouses", "nomenclatures", "recipes", "is_loaded"}
    assert client.get("/ui/").status_code == 200
    assert "/api/entities/{entity_type}/{code}" in spec["paths"]
    assert formats.status_code == 200 and formats.json()
    assert client.get("/api/get_default_report", params=params).status_code == 200
    for name in formats.json():
        report = client.get("/api/get_report", params={**params, "format": name})
        assert report.status_code == 200 and report.content, report.text
    assert client.put(f"/api/entities/groups/{entity['unique_code']}", json={"name": "Новое имя"}).status_code == 200
    assert "Новое имя" in client.get("/api/get_report", params={**params, "format": "TXT"}).text


def test_success_settings_use_general_deserialization_and_preserve_previous_on_error(tmp_path, monkeypatch):
    """<summary>Проверяет вызов общего восстановления настроек и сохранение прежней конфигурации при ошибке.</summary>"""
    # Подготовка
    monkeypatch.delattr(settings_manager, "instance", raising=False)
    calls = []
    original = deserializer.deserialize

    def restore(loader, source, model_type):
        """Фиксирует использование общей десериализации без подмены результата."""
        calls.append(model_type)
        return original(loader, source, model_type)

    monkeypatch.setattr(deserializer, "deserialize", restore)
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(CONFIG), encoding="utf-8")
    manager = settings_manager()

    # Действие
    manager.load(str(path))
    previous = manager.settings
    path.write_text(json.dumps({**CONFIG, "organization": False}), encoding="utf-8")
    with pytest.raises(argument_exception):
        manager.load(str(path))

    # Проверки
    assert calls == [settings_model, settings_model]
    assert manager.settings is previous

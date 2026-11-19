import json
from copy import deepcopy

import pytest

from Src.Core.common import common
from Src.Dtos.comparison_type_enum import comparison_type_enum
from Src.Dtos.filter_dto import filter_dto
from Src.Logics.convert_factory import convert_factory
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.deserializer import deserializer

from Tst.Integration.test_crud import client, create, ref


@pytest.mark.parametrize("collection", ["groups", "ranges", "nomenclatures", "recipes"])
def test_equals_filter_api_all_model_types_and_unchanged_source(client, collection):
    """<summary>Общий POST отбирает по имени и коду, не изменяя исходную коллекцию.</summary>"""
    # Подготовка
    before = client.get(f"/api/entities/{collection}").json()
    item = before[0]
    body = {"filters": [{"field": "name", "value": item["name"]},
                        {"field": "unique_code", "value": item["unique_code"]}]}

    # Действие
    response = client.post(f"/api/entities/{collection}/filter", json=body)
    all_items = client.post(f"/api/entities/{collection}/filter", json={})
    after = client.get(f"/api/entities/{collection}").json()

    # Проверки
    assert response.status_code == all_items.status_code == 200
    assert response.json() == [item]
    assert all_items.json() == before == after


def test_equals_filter_api_nested_recipes_units_and_like(client):
    """<summary>Поиск проходит по вложенному рецепту и базовой единице с точным или частичным сравнением.</summary>"""
    # Подготовка
    recipes = client.get("/api/entities/recipes").json()

    # Действие
    nested = client.post("/api/entities/recipes/filter", json={"filters": [
        {"field": "ingredients.ingredients.nomenclature.name", "value": "Сах", "comparison": "LIKE"},
    ]})
    units = client.post("/api/entities/ranges/filter", json={"filters": [
        {"field": "base_range.name", "value": "Грамм"},
    ]})
    absent = client.post("/api/entities/nomenclatures/filter", json={"filters": [
        {"field": "name", "value": "сах", "comparison": "LIKE"},
    ]})

    # Проверки
    assert nested.status_code == units.status_code == absent.status_code == 200
    assert nested.json() == [item for item in recipes if item["name"] == "Молочная карамель"]
    assert {item["name"] for item in units.json()} == {"Грамм", "Килограмм"}
    assert absent.json() == []


@pytest.mark.parametrize("body", [
    {"filters": [{"field": "name", "value": "x", "comparison": "UNKNOWN"}]},
    {"filters": [{"field": "name", "value": 123}]},
    {"filters": [{"field": "__class__.name", "value": "x"}]},
    {"filters": [{"field": "storage.missing.name", "value": "x"}]},
    {"filters": [{"field": "value", "value": "10"}]},
    {"filters": [{"value": "x"}]},
    {"filters": None},
    {"extra": True},
    [],
])
def test_raises_filter_api_invalid_requests_on_empty_collection(client, body):
    """<summary>Неверные DTO и пути дают HTTP 400 даже при отсутствии транзакций.</summary>"""
    # Подготовка
    assert client.get("/api/entities/transactions").json() == []

    # Действие
    response = client.post("/api/entities/transactions/filter", json=body)

    # Проверки
    assert response.status_code == 400, response.text
    assert client.get("/api/entities/transactions").json() == []


def test_raises_filter_api_unknown_collection(client):
    """<summary>Неизвестная коллекция отклоняется общей точкой получения данных.</summary>"""
    # Подготовка
    url = "/api/entities/unknown/filter"

    # Действие
    response = client.post(url, json={})

    # Проверки
    assert response.status_code == 400


@pytest.fixture
def movement_inputs(client):
    """Создаёт независимые справочники для проверки движений и ОСВ."""
    group = create(client, "groups", {"name": "Продукты ОСВ"})
    unit = create(client, "ranges", {"name": "Грамм ОСВ", "conversion_factor": 1})
    product = create(client, "nomenclatures", {
        "name": "Сахар ОСВ", "full_name": "Сахар ОСВ", "group": ref(group), "range": ref(unit),
    })
    storage = create(client, "warehouses", {"name": "Кухня ОСВ"})
    return {"nomenclature": ref(product), "storage": ref(storage)}


def test_success_transaction_crud_reference_protection_and_filter(client, movement_inputs):
    """<summary>Новый тип использует прежний CRUD, счётчики ссылок и общий прототип.</summary>"""
    # Подготовка
    body = {**movement_inputs, "value": 10, "period": "2026-11-01T12:00:00"}
    item = create(client, "transactions", body)
    url = f"/api/entities/transactions/{item['unique_code']}"
    product_url = f"/api/entities/nomenclatures/{movement_inputs['nomenclature']['ref']}"

    # Действие
    blocked = client.delete(product_url)
    invalid = client.put(url, json={**body, "value": 0})
    unchanged = client.get(url)
    updated = client.put(url, json={**body, "value": -4})
    selected = client.post("/api/entities/transactions/filter", json={"filters": [
        {"field": "nomenclature.name", "value": "Сахар ОСВ"},
    ]})
    deleted = client.delete(url)
    released = client.delete(product_url)

    # Проверки
    assert blocked.status_code == 409
    assert invalid.status_code == 400 and unchanged.json() == item
    assert updated.status_code == 200 and updated.json()["value"] == -4
    assert selected.status_code == 200 and selected.json() == [updated.json()]
    assert deleted.status_code == released.status_code == 204


def test_equals_turnover_api_filters_history_and_period_boundaries(client, movement_inputs):
    """<summary>ОСВ считает всю отфильтрованную историю и обороты периода из актуальных записей CRUD.</summary>"""
    # Подготовка
    for value, period in [(100, "2026-10-30T12:00"), (-20, "2026-10-31T23:59"),
                          (40, "2026-11-01T00:00"), (-30, "2026-11-30T23:59"),
                          (1000, "2026-12-01T00:00")]:
        create(client, "transactions", {**movement_inputs, "value": value, "period": period})
    other = create(client, "warehouses", {"name": "Другой склад ОСВ"})
    create(client, "transactions", {**movement_inputs, "storage": ref(other),
                                     "value": 999, "period": "2026-11-15"})
    body = {"start": "2026-11-01", "end": "2026-11-30", "filters": [
        {"field": "storage.unique_code", "value": movement_inputs["storage"]["ref"]},
        {"field": "nomenclature.name", "value": "Сахар ОСВ"},
    ]}

    # Действие
    response = client.post("/api/turnover", json=body)
    all_rows = client.post("/api/turnover", json={"start": body["start"], "end": body["end"]})
    snapshot = client.get("/api/entities/transactions").json()

    # Проверки
    assert response.status_code == all_rows.status_code == 200, response.text
    row, = response.json()
    assert row["storage"] == movement_inputs["storage"]
    assert row["nomenclature"] == movement_inputs["nomenclature"]
    assert (row["opening_balance"], row["income"], row["expense"], row["closing_balance"]) == (80, 40, 30, 90)
    assert len(all_rows.json()) == 2 and len(snapshot) == 6


@pytest.mark.parametrize("body", [
    {"start": "2026-12-01", "end": "2026-11-01"},
    {"start": "not-a-date", "end": "2026-11-01"},
    {"start": "2026-11-01"},
    {"start": "2026-11-01", "end": "2026-11-30", "filters": [{"field": "unknown.name", "value": "x"}]},
])
def test_raises_turnover_api_invalid_period_or_filter(client, body):
    """<summary>Неверный период и путь отклоняются до построения ОСВ.</summary>"""
    # Подготовка
    url = "/api/turnover"

    # Действие
    response = client.post(url, json=body)

    # Проверки
    assert response.status_code == 400, response.text


def test_equals_filter_dto_generic_serialization_round_trip():
    """<summary>DTO виден общей рефлексии и восстанавливается после JSON без отдельного конвертера.</summary>"""
    # Подготовка
    criteria = filter_dto("nomenclature.name", "Сах", comparison_type_enum.LIKE)
    factory = convert_factory()
    loader = deserializer(deserialize_factory())

    # Действие
    encoded = factory.create(criteria).convert(criteria)
    restored = loader.deserialize(json.loads(json.dumps(encoded)), filter_dto)

    # Проверки
    assert set(common.get_fields(criteria)) == {"field", "value", "comparison"}
    assert encoded == {"field": "nomenclature.name", "value": "Сах", "comparison": "LIKE"}
    assert restored.field == criteria.field and restored.value == criteria.value
    assert restored.comparison is comparison_type_enum.LIKE
    with pytest.raises(AttributeError):
        restored.field = "unique_code"


def test_equals_storage_snapshot_round_trip_current_crud_and_turnover(client, movement_inputs):
    """<summary>Один снимок восстанавливает актуальные справочники, транзакции, связи и результат ОСВ.</summary>"""
    # Подготовка
    import main

    original = {**movement_inputs, "value": 20, "period": "2026-10-31T23:59"}
    movement = create(client, "transactions", original)
    create(client, "transactions", {**original, "value": -5, "period": "2026-11-30T23:59"})
    period = {"start": "2026-11-01", "end": "2026-11-30"}
    saved = client.get("/api/storage/snapshot")
    balances = client.post("/api/turnover", json=period).json()
    url = f"/api/entities/transactions/{movement['unique_code']}"

    # Действие
    changed = client.put(url, json={**original, "value": 100})
    extra = create(client, "warehouses", {"name": "Не входит в снимок"})
    restored = client.post("/api/storage/snapshot", json=saved.json())
    after = client.get("/api/storage/snapshot")
    graph = main.crud.snapshot()
    transaction = next(item for item in graph["transactions"] if item.unique_code == movement["unique_code"])

    # Проверки
    assert saved.status_code == changed.status_code == after.status_code == 200
    assert restored.status_code == 204, restored.text
    assert after.json() == saved.json()
    assert client.get(url).json() == movement
    assert client.post("/api/turnover", json=period).json() == balances
    assert client.get(f"/api/entities/warehouses/{extra['unique_code']}").status_code == 404
    assert client.delete(f"/api/entities/nomenclatures/{movement_inputs['nomenclature']['ref']}").status_code == 409
    assert transaction.nomenclature is next(item for item in graph["nomenclatures"]
                                            if item.unique_code == transaction.nomenclature.unique_code)
    assert saved.json()["transactions"][0]["nomenclature"]["unique_code"] == movement_inputs["nomenclature"]["ref"]


@pytest.mark.parametrize("fault", ["missing", "unknown", "orphan", "conflict", "duplicate", "invalid"])
def test_unchanged_storage_snapshot_invalid_graph_is_atomic(client, movement_inputs, fault):
    """<summary>Неполный или противоречивый граф отклоняется без частичного изменения репозитория.</summary>"""
    # Подготовка
    create(client, "transactions", {**movement_inputs, "value": 10, "period": "2026-11-01T12:00"})
    before = client.get("/api/storage/snapshot").json()
    broken = deepcopy(before)
    if fault == "missing":
        del broken["transactions"]
    elif fault == "unknown":
        broken["unknown"] = []
    elif fault == "orphan":
        broken["warehouses"] = []
    elif fault == "conflict":
        broken["transactions"][0]["nomenclature"]["name"] = "Противоречие"
    elif fault == "duplicate":
        broken["transactions"].append(deepcopy(broken["transactions"][0]))
    else:
        broken["transactions"][0]["value"] = 0

    # Действие
    response = client.post("/api/storage/snapshot", json=broken)
    after = client.get("/api/storage/snapshot")

    # Проверки
    assert response.status_code in (400, 409), response.text
    assert after.status_code == 200 and after.json() == before


def test_separate_turnover_api_units_and_single_day_period(client, movement_inputs):
    """<summary>Один день включает обе границы, а движения одного товара в разных единицах не смешиваются.</summary>"""
    # Подготовка
    unit = create(client, "ranges", {"name": "Килограмм ОСВ", "conversion_factor": 1000,
                                      "base_range": client.get(f"/api/entities/nomenclatures/{movement_inputs['nomenclature']['ref']}").json()["range"]})
    for value, period in [(2, "2026-11-01T00:00"), (-1, "2026-11-01T23:59:59"),
                          (100, "2026-11-02T00:00")]:
        create(client, "transactions", {**movement_inputs, "range": ref(unit), "value": value, "period": period})
    create(client, "transactions", {**movement_inputs, "value": 5, "period": "2026-11-01T12:00"})

    # Действие
    response = client.post("/api/turnover", json={"start": "2026-11-01", "end": "2026-11-01"})

    # Проверки
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2
    row = next(item for item in response.json() if item["range"] == ref(unit))
    assert (row["opening_balance"], row["income"], row["expense"], row["closing_balance"]) == (0, 2, 1, 1)


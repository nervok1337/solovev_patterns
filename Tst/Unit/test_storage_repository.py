import pytest

from Src.Core.validator import operation_exception
from Src.Logics.storage_repository import storage_repository


def test_not_raise_repository_reference_lifecycle():
    """<summary>Проверяет загрузку в обратном порядке, защиту связей, замену ссылок, смену кода и удаление.</summary>"""
    # Подготовка
    repository = storage_repository({"nodes": object})
    repository.load([
        ("nodes", {"unique_code": "owner", "items": [{"ref": "target"}]}),
        ("nodes", {"unique_code": "target"}),
    ])

    # Действие
    with pytest.raises(operation_exception):
        repository.delete("nodes", "target")
    repository.update("nodes", "owner", {"unique_code": "owner", "items": []})
    released = repository.can_delete("nodes", "target")
    repository.update("nodes", "target", {"unique_code": "renamed"})
    repository.delete("nodes", "renamed")

    # Проверки
    assert released
    assert repository.codes("nodes") == ["owner"]
    for code in ("target", "renamed"):
        with pytest.raises(KeyError):
            repository.get("nodes", code)


def test_raises_repository_invalid_changes_are_atomic():
    """<summary>Отклоняет циклы, занятые коды, отсутствующие ссылки и смену используемого кода без частичной записи.</summary>"""
    # Подготовка
    repository = storage_repository({"nodes": object})
    owner = {"unique_code": "owner", "item": {"ref": "target"}}
    target = {"unique_code": "target"}
    repository.load([("nodes", owner), ("nodes", target)])

    # Действие
    with pytest.raises(ValueError, match="Цикл"):
        repository.update("nodes", "target", {**target, "item": {"ref": "owner"}})
    with pytest.raises(operation_exception):
        repository.update("nodes", "target", {"unique_code": "changed"})
    with pytest.raises(operation_exception):
        repository.create("nodes", target)
    with pytest.raises(ValueError):
        repository.create("nodes", {"unique_code": "new", "item": {"ref": "missing"}})

    # Проверки
    assert repository.get("nodes", "owner") == owner
    assert repository.get("nodes", "target") == target
    assert set(repository.codes("nodes")) == {"owner", "target"}
    assert not repository.can_delete("nodes", "target")


def test_equals_repository_instances_and_read_snapshots_are_independent():
    """<summary>Изменение полученной записи и другого экземпляра не меняет действующий индекс и счётчики.</summary>"""
    # Подготовка
    first = storage_repository({"nodes": object})
    second = storage_repository({"nodes": object})
    first.load([("nodes", {"unique_code": "owner", "items": [{"ref": "target"}]}),
                ("nodes", {"unique_code": "target"})])

    # Действие
    snapshot = first.get("nodes", "owner")
    snapshot["items"].clear()
    second.create("nodes", {"unique_code": "target"})
    second.delete("nodes", "target")

    # Проверки
    assert first.get("nodes", "owner")["items"] == [{"ref": "target"}]
    assert not first.can_delete("nodes", "target")
    assert second.codes("nodes") == []

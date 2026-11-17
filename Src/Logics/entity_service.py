from collections.abc import Callable

from Src.Core.abstract_storage import abstract_storage
from Src.Core.common import common
from Src.Core.entity_model import entity_model
from Src.Core.validator import operation_exception


class entity_service:
    """Сценарии CRUD: доменные ограничения и ссылки, без HTTP и JSON."""

    def __init__(self, storage: abstract_storage):
        """Принимает хранилище через абстрактный контракт."""
        self.__storage = storage

    def types(self):
        """Возвращает доступные типы коллекций."""
        return self.__storage.model_types()

    @staticmethod
    def __roots(storage):
        """Возвращает корневые объекты всех коллекций."""
        return [item for name in storage.model_types() for item in storage.entities(name)]

    @classmethod
    def __check_links(cls, storage, target):
        """Запрещает удаление и смену кода объекта с входящими ссылками."""
        for owner, linked in common.walk_links(cls.__roots(storage)):
            if owner is not target and linked is target:
                raise operation_exception("Сущность используется другим объектом")

    @classmethod
    def __validate(cls, storage):
        """Проверяет итоговое состояние всех доменных объектов."""
        for node in common.walk(cls.__roots(storage)):
            if isinstance(node, entity_model):
                node.validate()

    def list(self, collection):
        """Возвращает независимый снимок коллекции."""
        with self.__storage.transaction() as storage:
            return storage.entities(collection)

    def get(self, collection, code):
        """Возвращает независимый снимок сущности."""
        with self.__storage.transaction() as storage:
            return storage.get_entity(collection, code)

    def create(self, collection, build: Callable):
        """Строит и сохраняет проверенную сущность одной операцией."""
        with self.__storage.transaction() as storage:
            if collection not in storage.model_types():
                raise ValueError("Неизвестная коллекция")
            entity = build(storage.model_types()[collection], storage)
            storage.save_entity(collection, entity)
            self.__validate(storage)
            return entity

    def update(self, collection, code, build: Callable):
        """Проверяет кандидата, связи и атомарно обновляет исходный экземпляр."""
        with self.__storage.transaction() as storage:
            entity = storage.get_entity(collection, code)
            candidate = build(entity, storage)
            if candidate.unique_code != entity.unique_code:
                self.__check_links(storage, entity)
            storage.delete_entity(collection, code)
            entity.replace_with(candidate)
            storage.save_entity(collection, entity)
            self.__validate(storage)
            return entity

    def delete(self, collection, code):
        """Удаляет только неиспользуемую сущность."""
        with self.__storage.transaction() as storage:
            entity = storage.get_entity(collection, code)
            self.__check_links(storage, entity)
            storage.delete_entity(collection, code)

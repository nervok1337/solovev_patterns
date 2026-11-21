from Src.Dtos.filter_dto import filter_dto
from Src.Logics.deserialize_factory import deserialize_factory
from Src.Logics.deserializer import deserializer
from Src.Logics.prototype import prototype
from Src.Logics.turnover_prototype import turnover_prototype


class crud_service:
    """Выполняет сценарии CRUD через прослойку, не изменяя доменные модели."""

    def __init__(self, adapter):
        """Принимает адаптер существующего хранилища."""
        self.__adapter = adapter
        self.__repository = adapter.repository
        self.__loader = deserializer(deserialize_factory())

    def types(self):
        """Возвращает доступные коллекции доменных сущностей."""
        return list(self.__repository.types())

    def list(self, collection):
        """Возвращает согласованный снимок запрошенной коллекции."""
        with self.__repository.locked():
            return self.__adapter.list(collection)

    def __criteria(self, filters) -> list[filter_dto]:
        """Восстанавливает условия для всех сценариев через один механизм DTO."""
        return self.__loader.deserialize(filters, list[filter_dto])

    def select(self, collection, filters):
        """Фильтрует согласованный снимок любой коллекции общим прототипом."""
        criteria = self.__criteria(filters)
        items = self.list(collection)
        model_type = self.__repository.types()[collection]
        return prototype(items, model_type).clone(criteria)

    def turnover(self, filters, **period):
        """Передаёт исходные движения расчёту ОСВ до применения условий отбора."""
        criteria = self.__criteria(filters)
        return turnover_prototype(self.list("transactions"), **period).build(criteria)

    def snapshot(self) -> dict:
        """Читает полный согласованный снимок текущих данных, включая новые коллекции."""
        with self.__repository.locked():
            return self.__adapter.snapshot()

    def restore_snapshot(self, source: dict) -> None:
        """Проверяет и целиком восстанавливает снимок без частичных изменений."""
        with self.__repository.locked():
            collections = self.__loader.deserialize_collections(source, self.__repository.types())
            self.__adapter.restore_snapshot(collections)

    def get(self, collection, code):
        """Получает модель через индекс уникальных кодов."""
        with self.__repository.locked():
            return self.__adapter.get(collection, code)

    def find_entity(self, entity_type, code):
        """Разрешает прежние параметры отчётов через тот же индекс CRUD."""
        with self.__repository.locked():
            return self.__adapter.find_entity(entity_type, code)

    def create(self, collection, body):
        """Сначала проверяет модель, затем фиксирует запись и её ссылки."""
        with self.__repository.locked():
            candidate, record = self.__adapter.prepare(collection, body)
            self.__repository.create(collection, record)
            return candidate

    def update(self, collection, code, body):
        """Заменяет данные объекта с сохранением кода, если новый код не передан."""
        with self.__repository.locked():
            self.__repository.get(collection, code)
            candidate, record = self.__adapter.prepare(collection, body, code)
            self.__repository.update(collection, code, record)
            return candidate

    def delete(self, collection, code):
        """Удаляет только сущность без входящих ссылок."""
        self.__repository.delete(collection, code)

class crud_service:
    """Выполняет сценарии CRUD через прослойку, не изменяя доменные модели."""

    def __init__(self, adapter):
        """Принимает адаптер существующего хранилища."""
        self.__adapter = adapter
        self.__repository = adapter.repository

    def types(self):
        """Возвращает доступные коллекции доменных сущностей."""
        return list(self.__repository.types())

    def list(self, collection):
        """Возвращает согласованный снимок запрошенной коллекции."""
        with self.__repository.locked():
            return self.__adapter.list(collection)

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

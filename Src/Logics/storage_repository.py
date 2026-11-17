from collections import Counter
from collections.abc import Mapping
from contextlib import contextmanager
from copy import deepcopy
from threading import RLock

from Src.Core.validator import operation_exception


class storage_repository:
    """Индексирует записи сущностей, коллекции и входящие/исходящие ссылки."""

    def __init__(self, model_types: dict):
        """Создаёт независимое состояние одного экземпляра приложения."""
        self.__types = model_types.copy()
        self.__data = {}
        self.__collections = {name: {} for name in model_types}
        self.__links = {}
        self.__counts = Counter()
        self.__lock = RLock()

    @contextmanager
    def locked(self):
        """Объединяет подготовку и фиксацию операции под одной блокировкой."""
        with self.__lock:
            yield self

    def types(self) -> dict:
        """Возвращает зарегистрированные типы коллекций."""
        return self.__types.copy()

    def __collection(self, name):
        """Проверяет имя коллекции до обращения к индексам."""
        if name not in self.__collections:
            raise ValueError(f"Неизвестная коллекция: {name}")
        return self.__collections[name]

    @classmethod
    def __references(cls, value):
        """Извлекает коды ссылок из записи, включая вложенные коллекции."""
        if isinstance(value, Mapping):
            if set(value) == {"ref"}:
                yield value["ref"]
            else:
                for item in value.values():
                    yield from cls.__references(item)
        elif isinstance(value, list):
            for item in value:
                yield from cls.__references(item)

    def load(self, records):
        """Однократно загружает все корни и связи независимо от порядка записей."""
        with self.__lock:
            if self.__data:
                raise operation_exception("Начальные данные уже загружены")
            data, collections, links = {}, {name: {} for name in self.__types}, {}
            for collection, values in records:
                self.__collection(collection)
                code = values["unique_code"]
                if code in data:
                    raise operation_exception("Код сущности уже занят")
                data[code] = collection, deepcopy(values)
                collections[collection][code] = None
                links[code] = Counter(self.__references(values))
            counts = Counter()
            for targets in links.values():
                if not targets.keys() <= data.keys():
                    raise ValueError("Ссылка на отсутствующую сущность")
                counts.update(targets)
            self.__check_graph(links)
            self.__data, self.__collections = data, collections
            self.__links, self.__counts = links, counts

    @staticmethod
    def __check_graph(links):
        """Проверяет циклы начального графа без повторного раскрытия общих узлов."""
        visited, active = set(), set()

        def visit(code):
            """Проверяет один путь графа по индексам исходящих ссылок."""
            if code in active:
                raise ValueError("Цикл связей доменных сущностей")
            if code in visited:
                return
            active.add(code)
            for target in links[code]:
                visit(target)
            active.remove(code)
            visited.add(code)

        for code in links:
            visit(code)

    def get(self, collection, code) -> dict:
        """Находит запись по коду и проверяет принадлежность коллекции."""
        with self.__lock:
            self.__collection(collection)
            registered, values = self.__data[code]
            if registered != collection:
                raise KeyError(code)
            return deepcopy(values)

    def locate(self, code):
        """Разрешает ссылку непосредственно через индекс уникальных кодов."""
        with self.__lock:
            collection, values = self.__data[code]
            return collection, deepcopy(values)

    def codes(self, collection) -> list[str]:
        """Возвращает коды только запрошенной коллекции."""
        with self.__lock:
            return list(self.__collection(collection))

    def can_delete(self, collection, code) -> bool:
        """Проверяет входящий счётчик без обхода объектов и их свойств."""
        with self.__lock:
            self.__collection(collection)
            if self.__data[code][0] != collection:
                raise KeyError(code)
            return self.__counts[code] == 0

    def __prepare(self, collection, values, previous=None):
        """До записи проверяет код, ссылки и циклы, затрагивающие изменяемый узел."""
        self.__collection(collection)
        code = values["unique_code"]
        if code != previous and code in self.__data:
            raise operation_exception("Код сущности уже занят")
        targets = Counter(self.__references(values))
        if any(target not in self.__data and target != code for target in targets):
            raise ValueError("Ссылка на отсутствующую сущность")
        pending, visited = list(targets), set()
        while pending:
            target = pending.pop()
            if target == code or target == previous:
                raise ValueError("Цикл связей доменных сущностей")
            if target not in visited:
                visited.add(target)
                pending.extend(self.__links[target])
        return code, deepcopy(values), targets

    def create(self, collection, values):
        """Добавляет проверенную запись и учитывает только её исходящие ссылки."""
        with self.__lock:
            code, stored, targets = self.__prepare(collection, values)
            self.__data[code] = collection, stored
            self.__collections[collection][code] = None
            self.__links[code] = targets
            self.__counts.update(targets)

    def update(self, collection, previous, values):
        """Атомарно заменяет запись и изменяет счётчики на разницу связей."""
        with self.__lock:
            self.get(collection, previous)
            if values["unique_code"] != previous and self.__counts[previous]:
                raise operation_exception("Сущность используется другим объектом")
            code, stored, targets = self.__prepare(collection, values, previous)
            self.__counts.subtract(self.__links[previous])
            self.__counts.update(targets)
            if code != previous:
                del self.__data[previous]
                del self.__links[previous]
                del self.__collections[collection][previous]
                self.__counts.pop(previous, None)
            self.__data[code] = collection, stored
            self.__collections[collection][code] = None
            self.__links[code] = targets

    def delete(self, collection, code):
        """Удаляет свободную запись и снимает её исходящие ссылки."""
        with self.__lock:
            if not self.can_delete(collection, code):
                raise operation_exception("Сущность используется другим объектом")
            self.__counts.subtract(self.__links.pop(code))
            del self.__data[code]
            del self.__collections[collection][code]
            self.__counts.pop(code, None)

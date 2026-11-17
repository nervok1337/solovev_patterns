from collections import deque
from typing import get_args, get_type_hints

from Src.Core.common import common
from Src.Core.entity_model import entity_model
from Src.Logics.storage_repository import storage_repository


class storage_adapter:
    """Создаёт состояние CRUD из прежнего хранилища, не изменяя его интерфейс и выгрузку."""

    def __init__(self, storage, mapper, settings=None):
        """Однократно обнаруживает коллекции и индексирует их объекты и зависимости."""
        self.__mapper = mapper
        types, roots = {}, []
        sources = [storage] + ([] if settings is None else [settings])
        for source in sources:
            for name in common.get_fields(source):
                annotation = get_type_hints(getattr(type(source), name).fget).get("return")
                for model_type in self.__model_types(annotation):
                    types.setdefault(name, model_type)
                value = getattr(source, name)
                if isinstance(value, entity_model):
                    roots.append(value)
                elif common.is_collection(value):
                    roots.extend(value)
        pending = deque(types.values())
        visited_types = set()
        while pending:
            model_type = pending.popleft()
            if model_type in visited_types:
                continue
            visited_types.add(model_type)
            for name, annotation in mapper.fields(model_type).items():
                for related in self.__model_types(annotation):
                    if related not in types.values():
                        if name in types:
                            raise ValueError(f"Неоднозначная коллекция: {name}")
                        types[name] = related
                        pending.append(related)
        self.repository = storage_repository(types)
        collections = {model_type: name for name, model_type in types.items()}
        records, visited = [], set()
        while roots:
            entity = roots.pop()
            if id(entity) in visited:
                continue
            visited.add(id(entity))
            records.append((collections[type(entity)], mapper.record(entity)))
            roots.extend(mapper.dependencies(entity))
        self.repository.load(records)

    @classmethod
    def __model_types(cls, annotation):
        """Извлекает классы доменных сущностей из составных аннотаций."""
        if isinstance(annotation, type) and issubclass(annotation, entity_model):
            yield annotation
        for argument in get_args(annotation):
            yield from cls.__model_types(argument)

    def __resolver(self):
        """Создаёт независимый контекст чтения с общими экземплярами связанных моделей."""
        models = {}

        def resolve(code):
            """Восстанавливает объект по записи индекса без поиска по коллекциям."""
            if code not in models:
                collection, values = self.repository.locate(code)
                models[code] = self.__mapper.decode(values, self.repository.types()[collection], resolve)
            return models[code]

        return resolve

    def get(self, collection, code):
        """Возвращает независимую модель с актуальными значениями всех её зависимостей."""
        self.repository.get(collection, code)
        return self.__resolver()(code)

    def list(self, collection):
        """Восстанавливает запрошенную коллекцию в едином контексте чтения."""
        resolve = self.__resolver()
        return [resolve(code) for code in self.repository.codes(collection)]

    def prepare(self, collection, body, previous=None):
        """Проверяет кандидата существующими конструкторами до изменения индексов."""
        types = self.repository.types()
        if collection not in types:
            raise ValueError(f"Неизвестная коллекция: {collection}")
        if not isinstance(body, dict):
            raise ValueError("Ожидается объект запроса")
        values = body.copy()
        if previous is not None:
            values.setdefault("unique_code", previous)
        resolve = self.__resolver()
        candidate = self.__mapper.decode(values, types[collection], resolve)
        record = self.__mapper.record(candidate, previous)
        # Повторная сборка проверяет ограничения после нормализации самоссылки.
        candidate = self.__mapper.decode(record, types[collection], resolve)
        return candidate, record

    def find_entity(self, entity_type, code):
        """Сохраняет прежние псевдонимы отчётных API, используя новый индекс."""
        aliases = {name[:-1] if name.endswith("s") else name: name for name in self.repository.types()}
        aliases.update({"unit": "ranges", "unit_of_measurement": "ranges", "единица измерения": "ranges",
                        "номенклатура": "nomenclatures", "рецепт": "recipes"})
        collection = aliases.get(entity_type, entity_type)
        try:
            return self.get(collection, code), None, None
        except ValueError:
            return None, f"Неподдерживаемый тип: {entity_type}", 400
        except KeyError:
            return None, f"Сущность с кодом {code} не найдена", 404

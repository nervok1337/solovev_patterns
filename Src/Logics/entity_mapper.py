from collections.abc import Mapping
from enum import Enum
from functools import lru_cache
from inspect import isclass, signature
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints

from Src.Core.common import common
from Src.Core.entity_model import entity_model


class entity_mapper:
    """Использует существующие фабрики для преобразования CRUD без изменения моделей."""

    def __init__(self, deserializers, convertors):
        """Принимает фабрики восстановления и преобразования значений."""
        self.__deserializers = deserializers
        self.__convertors = convertors

    @staticmethod
    @lru_cache(maxsize=None)
    def fields(model_type) -> dict:
        """Получает входные поля из конструктора и свойств с сеттерами."""
        parameters = signature(model_type).parameters
        hints = get_type_hints(model_type.__init__)
        result = {name: hints[name] for name in parameters if name in hints}
        for name in common.get_fields(model_type):
            prop = getattr(model_type, name)
            if prop.fset is not None or name in parameters:
                result[name] = get_type_hints(prop.fget)["return"]
        return result

    @classmethod
    def __entities(cls, value):
        """Находит непосредственные доменные ссылки в значении поля."""
        if isinstance(value, entity_model):
            yield value
        elif isinstance(value, Mapping):
            for item in value.values():
                yield from cls.__entities(item)
        elif common.is_collection(value):
            for item in value:
                yield from cls.__entities(item)

    def dependencies(self, entity):
        """Раскрывает только поля одной сущности при начальной индексации."""
        for name in self.fields(type(entity)):
            yield from self.__entities(getattr(entity, name))

    def __value(self, value):
        """Кодирует ссылки как коды, а скаляры передаёт существующим конвертерам."""
        if isinstance(value, entity_model):
            return {"ref": value.unique_code}
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Mapping):
            return {name: self.__value(item) for name, item in value.items()}
        if common.is_collection(value):
            return [self.__value(item) for item in value]
        return self.__convertors.create(value).convert(value, "value")["value"]

    def record(self, entity, previous=None) -> dict:
        """Получает входную запись; самоссылка вместо необязательного значения хранится как None."""
        parameters = signature(type(entity)).parameters
        values = {}
        for name in self.fields(type(entity)):
            value = getattr(entity, name)
            parameter = parameters.get(name)
            if (isinstance(value, entity_model) and value.unique_code in (entity.unique_code, previous)
                    and parameter is not None and parameter.default is None):
                value = None
            values[name] = self.__value(value)
        return values

    def encode(self, entity) -> dict:
        """Возвращает публичные свойства, включая вычисляемые значения для API."""
        return {name: self.__value(getattr(entity, name)) for name in common.get_fields(entity)}

    def decode(self, values, model_type, resolve):
        """Восстанавливает модель, разрешая только существующие типизированные ссылки."""
        if not isinstance(values, dict) or not values.keys() <= self.fields(model_type).keys():
            raise ValueError("Неизвестные поля или неверный объект запроса")

        def restore(value, expected):
            """Разрешает ссылку по индексу либо делегирует тип существующей фабрике."""
            variants = get_args(expected) if get_origin(expected) in (Union, UnionType) else (expected,)
            models = tuple(item for item in variants
                           if isclass(item) and issubclass(item, entity_model))
            if isinstance(value, dict) and set(value) == {"ref"}:
                code = value["ref"]
                if not isinstance(code, str) or not code.strip():
                    raise ValueError("Нужен непустой код ссылки")
                try:
                    linked = resolve(code)
                except KeyError as error:
                    raise ValueError("Ссылка на отсутствующую сущность") from error
                if not models or not isinstance(linked, models):
                    raise ValueError("Неверный тип связанной сущности")
                return linked
            if isinstance(value, dict) and models:
                raise ValueError("Связанный объект передаётся как {ref: код}")
            return self.__deserializers.create(expected).restore(value, restore)

        return self.__deserializers.create(model_type).restore(values, restore)

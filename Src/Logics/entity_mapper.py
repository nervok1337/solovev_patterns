from collections.abc import Mapping
from enum import Enum
from inspect import isclass, signature
from types import UnionType
from typing import Union, get_args, get_origin

from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.abstract_deserialize_factory import abstract_deserialize_factory
from Src.Core.common import common
from Src.Core.entity_model import entity_model


class entity_mapper:
    """Адаптер данных CRUD к существующим фабрикам преобразования моделей."""

    def __init__(self, factory: abstract_deserialize_factory, convertors: abstract_convert_factory):
        """Принимает абстрактные фабрики без создания конкретных зависимостей."""
        self.__factory = factory
        self.__convertors = convertors

    @staticmethod
    def __input_fields(model_type):
        """Находит параметры конструктора и свойства с сеттером через рефлексию."""
        return set(signature(model_type).parameters) | {
            name for name in common.get_fields(model_type)
            if getattr(model_type, name).fset is not None
        }

    def decode(self, data, model_type, storage):
        """Создаёт модель и разрешает типизированные ссылки в объекты хранилища."""
        if not isinstance(data, dict) or not data.keys() <= self.__input_fields(model_type):
            raise ValueError("Неизвестные поля или неверный объект запроса")

        def restore(value, expected):
            """Передаёт обычные значения фабрике, а ссылки разрешает по ожидаемому типу."""
            variants = get_args(expected) if get_origin(expected) in (Union, UnionType) else (expected,)
            if isinstance(value, dict) and set(value) == {"ref"}:
                if not isinstance(value["ref"], str) or not value["ref"].strip():
                    raise ValueError("Нужен непустой код ссылки")
                found = [item for name, registered in storage.model_types().items()
                         if any(isclass(variant) and issubclass(registered, variant) for variant in variants)
                         for item in storage.entities(name) if item.unique_code == value["ref"]]
                if len(found) != 1:
                    raise ValueError("Ссылка отсутствует или имеет неверный тип")
                return found[0]
            if isinstance(value, dict) and any(
                isclass(variant) and issubclass(variant, entity_model) for variant in variants
            ):
                raise ValueError("Связанный объект передаётся как {ref: код}")
            return self.__factory.create(expected).restore(value, restore)

        return self.__factory.create(model_type).restore(data, restore)

    def __value(self, value):
        """Преобразует ссылки и коллекции, а скаляры передаёт общим конвертерам."""
        if isinstance(value, entity_model):
            return {"ref": value.unique_code}
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Mapping):
            return {name: self.__value(item) for name, item in value.items()}
        if common.is_collection(value):
            return [self.__value(item) for item in value]
        return self.__convertors.create(value).convert(value, "value")["value"]

    def encode(self, entity):
        """Возвращает публичные поля модели с кодами связанных объектов."""
        return {name: self.__value(getattr(entity, name)) for name in common.get_fields(entity)}

    def updated(self, original, data, storage):
        """Строит кандидат для PUT без изменения живого объекта."""
        if not isinstance(data, dict):
            raise ValueError("Ожидается объект запроса")
        identity = entity_model.unique_code.fget.__name__
        values = {identity: original.unique_code}
        values.update(data)
        return self.decode(values, type(original), storage)

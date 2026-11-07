from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, time
from enum import Enum
from inspect import Parameter, isclass, signature
from math import isfinite
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from Src.Core.abstract_deserializer import (
    abstract_deserialize_factory, abstract_model_deserializer, restore_model,
)
from Src.Core.common import common
from Src.Core.exception import arguments_exception


class value_deserializer(abstract_model_deserializer):
    def __init__(self, model_type):
        self.model_type = model_type

    def matches(self, source: object) -> bool:
        return type(source) is self.model_type or (
            self.model_type is float and type(source) is int
        )

    def restore(self, source: object, restore: restore_model) -> object:
        if not self.matches(source):
            raise arguments_exception("source", f"Ожидается {self.model_type}!")
        if self.model_type is float:
            try:
                value = float(source)
            except OverflowError as error:
                raise arguments_exception("source", "Число слишком велико!") from error
            if not isfinite(value):
                raise arguments_exception("source", "Ожидается конечное число!")
            return value
        return source


class text_deserializer(value_deserializer):
    """Стандартные типы с текстовым JSON-представлением."""

    def matches(self, source: object) -> bool:
        return isinstance(source, str)

    def restore(self, source: object, restore: restore_model) -> object:
        if not self.matches(source):
            raise arguments_exception("source", "Ожидается строка!")
        if issubclass(self.model_type, Enum):
            return self.model_type(source)
        return self.model_type.fromisoformat(source)


class collection_deserializer(value_deserializer):
    def matches(self, source: object) -> bool:
        origin = get_origin(self.model_type) or self.model_type
        return isinstance(source, dict if origin in (dict, Mapping) else list)

    def restore(self, source: object, restore: restore_model) -> object:
        if not self.matches(source):
            raise arguments_exception("source", "Неверный тип коллекции!")
        origin = get_origin(self.model_type) or self.model_type
        types = get_args(self.model_type)
        if origin in (dict, Mapping):
            key_type, value_type = types or (str, Any)
            return {restore(key, key_type): restore(value, value_type)
                    for key, value in source.items()}
        item_type = types[0] if types else Any
        values = [restore(item, item_type) for item in source]
        if origin in (set, frozenset):
            return origin(values)
        return values


class union_deserializer(value_deserializer):
    def __init__(self, model_type, factory: abstract_deserialize_factory):
        super().__init__(model_type)
        self.factory = factory

    def matches(self, source: object) -> bool:
        return any(self.factory.create(item).matches(source)
                   for item in get_args(self.model_type))

    def restore(self, source: object, restore: restore_model) -> object:
        candidates = [item for item in get_args(self.model_type)
                      if self.factory.create(item).matches(source)]
        if type(source) in candidates:
            return restore(source, type(source))
        if len(candidates) != 1:
            raise arguments_exception("source", "Нельзя однозначно выбрать тип из Union!")
        return restore(source, candidates[0])


class dynamic_deserializer(value_deserializer):
    def matches(self, source: object) -> bool:
        return common.is_simple_value(source) or isinstance(source, (list, dict))

    def restore(self, source: object, restore: restore_model) -> object:
        # Без аннотации конкретной модели сохраняем обычные JSON-значения.
        if not self.matches(source):
            raise arguments_exception("source", "Ожидается JSON-значение!")
        return restore(source, type(source))


class reference_deserializer(value_deserializer):
    """Получает схему объекта из конструктора, свойств и аннотаций класса."""

    def __init__(self, model_type):
        super().__init__(model_type)
        self.parameters = {
            name: parameter for name, parameter in signature(model_type).parameters.items()
            if parameter.kind not in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD)
        }
        self.properties = {
            name: getattr(model_type, name) for name in common.get_fields(model_type)
        }
        self.types = {name: hint for name, hint in get_type_hints(model_type).items()
                      if not name.startswith("_")}
        for name, prop in self.properties.items():
            hint = get_type_hints(prop.fget).get("return")
            if hint is not None:
                self.types[name] = hint
        # Конструктор точнее описывает вход: например, допускает None для базы.
        self.types.update({name: hint for name, hint in get_type_hints(model_type.__init__).items()
                           if name in self.parameters})
        self.fields = set(self.parameters) | set(self.properties) | set(self.types)
        self.required = {name for name, param in self.parameters.items()
                         if param.default is Parameter.empty}

    def matches(self, source: object) -> bool:
        return (isinstance(source, dict) and self.required <= source.keys()
                and source.keys() <= self.fields)

    def restore(self, source: object, restore: restore_model) -> object:
        if not self.matches(source):
            raise arguments_exception("source", f"Неверные поля {self.model_type.__name__}!")
        values = {}
        for name, value in source.items():
            if name not in self.types:
                raise arguments_exception(name, "Для восстановления нужна аннотация типа!")
            values[name] = restore(value, self.types[name])
        positional = [values[name] if name in values else param.default
                      for name, param in self.parameters.items()
                      if param.kind is Parameter.POSITIONAL_ONLY]
        keywords = {name: values[name] for name, param in self.parameters.items()
                    if name in values and param.kind is not Parameter.POSITIONAL_ONLY}
        model = self.model_type(*positional, **keywords)
        for name, value in values.items():
            if name in self.parameters:
                continue
            prop = self.properties.get(name)
            if prop is None or prop.fset is not None:
                setattr(model, name, value)
        # Вычисляемые свойства проверяем после заполнения всех изменяемых полей.
        for name, prop in self.properties.items():
            if name in values and name not in self.parameters and prop.fset is None:
                if getattr(model, name) != values[name]:
                    raise arguments_exception(name, "Вычисляемое свойство не совпадает с данными!")
        return model


class deserialize_factory(abstract_deserialize_factory):
    """Выбирает категорию обработчика; о доменных классах и их полях не знает."""

    def create(self, model_type: Any) -> abstract_model_deserializer:
        origin = get_origin(model_type) or model_type
        if model_type in (Any, object):
            return dynamic_deserializer(model_type)
        if origin in (Union, UnionType):
            return union_deserializer(model_type, self)
        if origin in (list, set, frozenset, Iterable, Sequence, dict, Mapping):
            return collection_deserializer(model_type)
        if model_type in (str, int, float, bool, type(None)):
            return value_deserializer(model_type)
        if isclass(model_type):
            if issubclass(model_type, (Enum, date, datetime, time)):
                return text_deserializer(model_type)
            return reference_deserializer(model_type)
        raise arguments_exception("model_type", f"Неподдерживаемая аннотация {model_type}!")

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, time
from enum import Enum
from inspect import isclass
from types import UnionType
from typing import Any, Union, get_origin

from Src.Core.abstract_deserialize_factory import abstract_deserialize_factory
from Src.Core.abstract_model_deserializer import abstract_model_deserializer
from Src.Core.exception import arguments_exception
from Src.Logics.collection_deserializer import collection_deserializer
from Src.Logics.dynamic_deserializer import dynamic_deserializer
from Src.Logics.reference_deserializer import reference_deserializer
from Src.Logics.text_deserializer import text_deserializer
from Src.Logics.union_deserializer import union_deserializer
from Src.Logics.value_deserializer import value_deserializer


class deserialize_factory(abstract_deserialize_factory):
    """Выбирает категорию обработчика; о доменных классах и их полях не знает."""

    def create(self, model_type: Any) -> abstract_model_deserializer:
        """Создаёт обработчик по категории ожидаемого типа, не преобразуя данные."""
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

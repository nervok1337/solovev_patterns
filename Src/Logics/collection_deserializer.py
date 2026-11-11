from collections.abc import Mapping
from typing import Any, get_args, get_origin

from Src.Core.abstract_model_deserializer import restore_model
from Src.Core.exception import arguments_exception
from Src.Logics.value_deserializer import value_deserializer


class collection_deserializer(value_deserializer):
    """Восстанавливает коллекцию, определяя типы элементов по аннотации."""
    def matches(self, source: object) -> bool:
        """Проверяет, соответствует ли словарь или список ожидаемому виду коллекции."""
        origin = get_origin(self.model_type) or self.model_type
        return isinstance(source, dict if origin in (dict, Mapping) else list)

    def restore(self, source: object, restore: restore_model) -> object:
        """Рекурсивно восстанавливает элементы коллекции, а для словаря также ключи."""
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

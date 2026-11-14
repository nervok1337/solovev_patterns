from collections.abc import Mapping, Sequence, Set
from inspect import signature
from typing import get_type_hints

from Src.Core.validator import argument_exception


class common:
    """Предоставляет общие операции для работы с моделями."""

    @staticmethod
    def is_collection(value: object) -> bool:
        """Проверяет, является ли значение коллекцией, но не строкой."""
        return isinstance(value, (Mapping, Sequence, Set)) and not isinstance(
            value, (str, bytes, bytearray)
        )

    @staticmethod
    def is_simple_value(value: object) -> bool:
        """Проверяет строку, число, логическое или пустое значение."""
        return value is None or isinstance(value, (str, int, float, bool))

    @staticmethod
    def get_fields(source, is_common: bool = False) -> list[str]:
        """Возвращает публичные свойства; для класса не вызывает геттеры.

        Фильтрация is_common по значениям применяется только к экземплярам.
        """
        if source is None:
            raise argument_exception("Некорректно переданы аргументы!")

        source_type = source if isinstance(source, type) else type(source)
        fields = []
        for name in filter(lambda item: not item.startswith("_"), dir(source)):
            attribute = getattr(source_type, name, None)
            if not isinstance(attribute, property):
                continue

            if (not isinstance(source, type) and is_common
                    and common.is_collection(getattr(source, name))):
                continue

            fields.append(name)

        return fields

    @staticmethod
    def get_annotations(model_type: type) -> dict:
        """Получает типы параметров конструктора и публичных свойств модели."""
        hints = get_type_hints(model_type.__init__)
        result = {name: hints[name] for name in signature(model_type).parameters if name in hints}
        for name in common.get_fields(model_type):
            hint = get_type_hints(getattr(model_type, name).fget).get("return")
            if hint is not None and name not in result:
                result[name] = hint
        return result

    @staticmethod
    def walk(source: object):
        """Обходит публичный граф объектов без повторного посещения узлов."""
        pending = [source]
        visited = {}
        while pending:
            value = pending.pop()
            if id(value) in visited:
                continue
            visited[id(value)] = value
            yield value
            if isinstance(value, Mapping):
                pending.extend(value.values())
            elif common.is_collection(value):
                pending.extend(value)
            elif value is not None:
                pending.extend(getattr(value, name) for name in common.get_fields(value))

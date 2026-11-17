from collections.abc import Iterable, Mapping, Sequence, Set
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
    def __children(source: object):
        """Возвращает непосредственные значения коллекции или публичных свойств."""
        if isinstance(source, Mapping):
            yield from source.values()
        elif common.is_collection(source):
            yield from source
        elif source is not None:
            for name in common.get_fields(source):
                yield getattr(source, name)

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
            pending.extend(common.__children(value))

    @staticmethod
    def walk_links(roots: Iterable[object]):
        """Выдаёт все рёбра графа, раскрывая каждый узел один раз для всех корней.

        Сам список корней не образует связей. Ребро выдаётся и для уже
        посещённого узла; словарь удерживает временные значения свойств.
        """
        pending = list(roots)
        visited = {}
        while pending:
            owner = pending.pop()
            if id(owner) in visited:
                continue
            visited[id(owner)] = owner
            for linked in common.__children(owner):
                yield owner, linked
                if id(linked) not in visited:
                    pending.append(linked)

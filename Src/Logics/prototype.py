from collections.abc import Iterable, Mapping
from copy import copy
from operator import contains, eq
from typing import Generic, Self, TypeVar, get_args, get_type_hints

from Src.Core.common import common
from Src.Dtos.comparison_type_enum import comparison_type_enum
from Src.Dtos.filter_dto import filter_dto
from Src.Logics.convert_factory import convert_factory

T = TypeVar("T")


class prototype(Generic[T]):
    """Хранит снимок состава коллекции и клонирует его с условиями отбора."""

    __comparisons = {
        comparison_type_enum.EQUALS: eq,
        comparison_type_enum.LIKE: contains,
    }

    def __init__(self, source: Iterable[T], model_type: type[T]) -> None:
        """Запоминает тип для проверки фильтра независимо от наличия записей."""
        self._items = tuple(source)
        self.__model_type = model_type
        self.__convertors = convert_factory()

    @property
    def data(self) -> list[T]:
        """Возвращает отдельный список с выбранными доменными объектами."""
        return list(self._items)

    def clone(self, filters: list[filter_dto]) -> Self:
        """Копирует прототип с сохранением подтипа; модели не изменяются и не дублируются."""
        for condition in filters:
            if not isinstance(condition, filter_dto):
                raise ValueError("Ожидается DTO условия фильтрации")
            if not self.__has_path(self.__model_type, condition.field.split(".")):
                raise ValueError(f"Неизвестное поле фильтра: {condition.field}")
        result = copy(self)
        result._items = tuple(
            item for item in self._items
            if all(self.__matches(item, condition) for condition in filters)
        )
        return result

    @classmethod
    def __has_path(cls, annotation, parts: list[str]) -> bool:
        """Проверяет путь рефлексией, включая пустые коллекции и объединения типов."""
        arguments = get_args(annotation)
        if arguments:
            return any(cls.__has_path(item, parts) for item in arguments)
        if not isinstance(annotation, type) or parts[0] not in common.get_fields(annotation):
            return False
        field_type = get_type_hints(getattr(annotation, parts[0]).fget).get("return")
        return True if len(parts) == 1 else cls.__has_path(field_type, parts[1:])

    def __matches(self, source: object, condition: filter_dto) -> bool:
        """Проверяет условие хотя бы для одного значения указанного пути."""
        compare = self.__comparisons[condition.comparison]
        for value in self.__values(source, tuple(condition.field.split(".")), set()):
            value = self.__convertors.create(value).convert(value, "value")["value"]
            if condition.comparison is comparison_type_enum.LIKE:
                if not isinstance(value, str) or not isinstance(condition.value, str):
                    continue
            if compare(value, condition.value):
                return True
        return False

    @classmethod
    def __values(cls, source: object, parts: tuple[str, ...], active: set):
        """Обходит публичные свойства и коллекции с защитой от циклов."""
        key = id(source), parts
        if source is None or key in active:
            return
        active.add(key)
        try:
            if common.is_collection(source):
                items = source.values() if isinstance(source, Mapping) else source
                for item in items:
                    yield from cls.__values(item, parts, active)
            elif parts[0] in common.get_fields(type(source)):
                value = getattr(source, parts[0])
                if len(parts) == 1:
                    yield value
                else:
                    yield from cls.__values(value, parts[1:], active)
        finally:
            active.remove(key)

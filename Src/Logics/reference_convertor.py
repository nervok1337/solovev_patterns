from collections.abc import Mapping
from datetime import date, datetime, time

from Src.Core.abstract_covertor import abstract_covertor
from Src.Core.common import common
from Src.Core.validator import argument_exception
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor


class reference_convertor(abstract_covertor):
    """Преобразует ссылки и коллекции объекта во вложенные структуры."""

    def __init__(self) -> None:
        """Подготавливает конвертеры простых свойств вложенных объектов."""
        self.__value_convertors: list[abstract_covertor] = [
            basic_convertor(),
            datetime_convertor(),
        ]

    def convert(self, source: object) -> dict[str, object]:
        """Возвращает ссылочные свойства, сохраняя вложенность объектов."""
        converted_fields = self.__convert_value_fields(source)
        return self.__convert_references(source, [source], converted_fields)

    def __convert_value_fields(self, source: object) -> dict[str, object]:
        """Объединяет результаты существующих конвертеров значений."""
        result: dict[str, object] = {}
        for convertor in self.__value_convertors:
            result.update(convertor.convert(source))
        return result

    def __convert_references(
        self,
        source: object,
        ancestors: list[object],
        converted_fields: dict[str, object],
    ) -> dict[str, object]:
        """Преобразует поля, которые не обработали конвертеры значений."""
        result: dict[str, object] = {}
        for field in common.get_fields(source):
            if field not in converted_fields:
                result[field] = self.__convert_value(getattr(source, field), ancestors)

        return result

    def __convert_value(self, value: object, ancestors: list[object]) -> object:
        """Преобразует вложенное значение с проверкой циклических ссылок."""
        if common.is_simple_value(value):
            return value
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()

        for ancestor in ancestors:
            if value is ancestor:
                return self.__create_reference(value)

        path = ancestors.copy()
        path.append(value)

        if isinstance(value, Mapping):
            result: dict[str, object] = {}
            for key, item in value.items():
                result[key] = self.__convert_value(item, path)
            return result

        if common.is_collection(value):
            items = []
            for item in value:
                items.append(self.__convert_value(item, path))
            return items

        if not common.get_fields(value):
            raise argument_exception(
                f"Неподдерживаемый тип ссылочного значения: {type(value).__name__}"
            )

        result = self.__convert_value_fields(value)
        result.update(self.__convert_references(value, path, result))
        return result

    @staticmethod
    def __create_reference(value: object) -> dict[str, object]:
        """Представляет циклическую ссылку уникальным кодом объекта."""
        unique_code = getattr(value, "unique_code", None)
        if unique_code is None:
            raise argument_exception(
                "Нельзя преобразовать циклическую ссылку без unique_code"
            )
        return {"unique_code": unique_code}

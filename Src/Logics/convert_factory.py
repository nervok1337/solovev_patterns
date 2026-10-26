from datetime import date, datetime, time

from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.abstract_covertor import abstract_covertor
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor


class convert_factory(abstract_convert_factory):
    """Выбирает конвертер значения без выполнения преобразования."""

    def __init__(self) -> None:
        """Регистрирует конвертеры простых типов и даты со временем."""
        self.__convertors: dict[type, type[abstract_covertor]] = {
            str: basic_convertor,
            int: basic_convertor,
            float: basic_convertor,
            bool: basic_convertor,
            type(None): basic_convertor,
            datetime: datetime_convertor,
            date: datetime_convertor,
            time: datetime_convertor,
        }

    def create(
        self, source: object, ancestors: list[object] | None = None
    ) -> abstract_covertor:
        """Возвращает конвертер по типу значения с учётом наследования."""
        for source_type in type(source).__mro__:
            convertor_type = self.__convertors.get(source_type)
            if convertor_type is not None:
                return convertor_type()

        return reference_convertor(self, ancestors)

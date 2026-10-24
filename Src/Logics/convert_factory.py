from Src.Core.abstract_covertor import abstract_covertor
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor


class convert_factory:
    """Формирует словарь объекта с помощью конвертеров его свойств."""

    def __init__(self) -> None:
        """Регистрирует конвертеры простых полей, дат и ссылок."""
        self.__convertors: list[abstract_covertor] = [
            basic_convertor(),
            datetime_convertor(),
            reference_convertor(),
        ]

    def create(self, source: object) -> dict[str, object]:
        """Объединяет преобразованные поля, сохраняя структуру объекта."""
        result: dict[str, object] = {}
        for convertor in self.__convertors:
            result.update(convertor.convert(source))

        return result

from datetime import date, datetime, time

from Src.Core.abstract_covertor import abstract_covertor
from Src.Core.common import common


class datetime_convertor(abstract_covertor):
    """Преобразует свойства даты и времени объекта в словарь."""

    def convert(self, source: object) -> dict[str, object]:
        """Возвращает даты и время в строковом формате ISO 8601."""
        result: dict[str, object] = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            if isinstance(value, (datetime, date, time)):
                result[field] = value.isoformat()

        return result

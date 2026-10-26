from datetime import date, datetime, time

from Src.Core.abstract_covertor import abstract_covertor
from Src.Core.validator import argument_exception


class datetime_convertor(abstract_covertor):
    """Преобразует дату или время в именованное поле словаря."""

    def convert(
        self, source: object, field_name: str | None = None
    ) -> dict[str, object]:
        """Сохраняет дату или время в строковом формате ISO 8601."""
        if not isinstance(source, (datetime, date, time)):
            raise argument_exception("Ожидается дата или время")

        key = "value" if field_name is None else field_name
        return {key: source.isoformat()}

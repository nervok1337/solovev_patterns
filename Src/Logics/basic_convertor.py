from Src.Core.abstract_covertor import abstract_covertor
from Src.Core.common import common


class basic_convertor(abstract_covertor):
    """Преобразует простые свойства объекта в словарь."""

    def convert(self, source: object) -> dict[str, object]:
        """Возвращает строки, числа, логические значения и пустые поля."""
        result: dict[str, object] = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            if common.is_simple_value(value):
                result[field] = value

        return result

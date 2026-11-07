from Src.Core.abstract_covertor import abstract_covertor
from Src.Core.common import common
from Src.Core.validator import argument_exception


class basic_convertor(abstract_covertor):
    """Преобразует простое значение в именованное поле словаря."""

    def convert(
        self, source: object, field_name: str | None = None
    ) -> dict[str, object]:
        """Сохраняет простое значение под именем поля или ключом value."""
        if source is None and field_name is None:
            raise argument_exception("Некорректно переданы аргументы!")
        if not common.is_simple_value(source):
            raise argument_exception("Ожидается простое значение")

        key = "value" if field_name is None else field_name
        return {key: source}

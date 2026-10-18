from collections.abc import Mapping, Sequence, Set

from Src.Core.validator import argument_exception


class common:
    """Предоставляет общие операции для работы с моделями."""

    @staticmethod
    def get_fields(source, is_common: bool = False) -> list[str]:
        """Возвращает имена публичных свойств объекта через рефлексию."""
        if source is None:
            raise argument_exception("Некорректно переданы аргументы!")

        fields = []
        for name in filter(lambda item: not item.startswith("_"), dir(source)):
            attribute = getattr(source.__class__, name, None)
            if not isinstance(attribute, property):
                continue

            value = getattr(source, name)
            is_collection = isinstance(value, (Mapping, Sequence, Set))
            if isinstance(value, (str, bytes, bytearray)):
                is_collection = False

            if is_common and is_collection:
                continue

            fields.append(name)

        return fields

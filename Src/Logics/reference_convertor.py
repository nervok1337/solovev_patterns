from collections.abc import Mapping

from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.abstract_covertor import abstract_covertor
from Src.Core.common import common
from Src.Core.validator import argument_exception


class reference_convertor(abstract_covertor):
    """Преобразует составной объект, поручая обработку полей конвертерам."""

    def __init__(
        self,
        factory: abstract_convert_factory,
        ancestors: list[object] | None = None,
    ) -> None:
        """Принимает фабрику и текущую цепочку вложенных объектов."""
        self.__factory = factory
        self.__ancestors = [] if ancestors is None else ancestors.copy()

    def convert(
        self, source: object, field_name: str | None = None
    ) -> dict[str, object]:
        """Сохраняет составной объект и имена его вложенных полей."""
        result = self.__convert_reference(source)
        if field_name is not None:
            return {field_name: result}
        if isinstance(result, dict):
            return result
        return {"value": result}

    def __convert_reference(self, source: object) -> object:
        """Обходит структуру, делегируя каждое значение выбранному обработчику."""
        for ancestor in self.__ancestors:
            if source is ancestor:
                return self.__create_reference(source)

        path = self.__ancestors.copy()
        path.append(source)

        if isinstance(source, Mapping):
            fields = source
        elif common.is_collection(source):
            items = []
            for item in source:
                convertor = self.__factory.create(item, path)
                items.append(convertor.convert(item, "value")["value"])
            return items
        else:
            fields = {}
            for field in common.get_fields(source):
                fields[field] = getattr(source, field)
            if not fields:
                raise argument_exception(
                    f"Неподдерживаемый тип ссылочного значения: {type(source).__name__}"
                )

        result: dict[str, object] = {}
        for name, value in fields.items():
            convertor = self.__factory.create(value, path)
            result.update(convertor.convert(value, name))
        return result

    @staticmethod
    def __create_reference(value: object) -> dict[str, object]:
        """Представляет цикл прежним способом до уточнения правила сериализации."""
        unique_code = getattr(value, "unique_code", None)
        if unique_code is None:
            raise argument_exception(
                "Нельзя преобразовать циклическую ссылку без unique_code"
            )
        return {"unique_code": unique_code}

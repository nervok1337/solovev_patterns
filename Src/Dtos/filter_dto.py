from Src.Dtos.comparison_type_enum import comparison_type_enum


class filter_dto:
    """Одно условие по имени или коду, включая путь через вложенные свойства."""

    def __init__(self, field: str, value: str,
                 comparison: comparison_type_enum = comparison_type_enum.EQUALS) -> None:
        """Отклоняет неверную операцию и доступ к непубличным или лишним полям."""
        if not isinstance(field, str):
            raise ValueError("Поле фильтра должно быть строкой")
        parts = field.split(".")
        if (any(not part.isidentifier() or part.startswith("_") for part in parts)
                or parts[-1] not in ("name", "unique_code")):
            raise ValueError("Путь фильтра должен завершаться name или unique_code")
        if not isinstance(value, str):
            raise ValueError("Значение фильтра должно быть строкой")
        if not isinstance(comparison, comparison_type_enum):
            raise ValueError("Неизвестная операция сравнения")
        self.__field = field
        self.__value = value
        self.__comparison = comparison

    @property
    def field(self) -> str:
        """Публичный путь к проверяемому свойству модели."""
        return self.__field

    @property
    def value(self) -> str:
        """Строка для точного или частичного сравнения."""
        return self.__value

    @property
    def comparison(self) -> comparison_type_enum:
        """Операция сравнения выбранного свойства."""
        return self.__comparison


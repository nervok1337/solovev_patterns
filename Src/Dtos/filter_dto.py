from Src.Dtos.comparison_type_enum import comparison_type_enum


class filter_dto:
    """Одно условие по публичному свойству, включая путь через вложенные модели."""

    def __init__(self, field: str, value: object,
                 comparison: comparison_type_enum = comparison_type_enum.EQUALS) -> None:
        """Проверяет описание условия; существование свойства определяет прототип."""
        if not isinstance(field, str) or not field:
            raise ValueError("Поле фильтра должно быть непустой строкой")
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
    def value(self) -> object:
        """Значение свойства в представлении JSON для сравнения."""
        return self.__value

    @property
    def comparison(self) -> comparison_type_enum:
        """Операция сравнения выбранного свойства."""
        return self.__comparison

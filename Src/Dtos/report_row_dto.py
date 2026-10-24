class report_row_dto:
    """Хранит значения одной строки отчёта в порядке столбцов."""

    def __init__(self, values: list[object]) -> None:
        """Инициализирует значения строки отчёта."""
        self.__values = values

    @property
    def values(self) -> list[object]:
        """Возвращает значения ячеек строки."""
        return self.__values

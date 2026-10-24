from Src.Dtos.report_row_dto import report_row_dto


class report_data_dto:
    """Хранит унифицированные данные для форматирования отчёта."""

    def __init__(
        self,
        root_name: str,
        row_name: str | None,
        name: str,
        keys: list[str],
        headers: list[str],
        rows: list[report_row_dto],
        numeric_columns: frozenset[int] = frozenset(),
    ) -> None:
        """Инициализирует данные отчёта со строками в виде DTO."""
        self.__root_name = root_name
        self.__row_name = row_name
        self.__name = name
        self.__keys = keys
        self.__headers = headers
        self.__rows = rows
        self.__numeric_columns = numeric_columns

    @property
    def root_name(self) -> str:
        """Возвращает имя корневого элемента отчёта."""
        return self.__root_name

    @property
    def row_name(self) -> str | None:
        """Возвращает имя элемента строки, если оно задано."""
        return self.__row_name

    @property
    def name(self) -> str:
        """Возвращает наименование объекта отчёта."""
        return self.__name

    @property
    def keys(self) -> list[str]:
        """Возвращает имена полей строк отчёта."""
        return self.__keys

    @property
    def headers(self) -> list[str]:
        """Возвращает заголовки столбцов отчёта."""
        return self.__headers

    @property
    def rows(self) -> list[report_row_dto]:
        """Возвращает строки данных отчёта."""
        return self.__rows

    @property
    def numeric_columns(self) -> frozenset[int]:
        """Возвращает индексы числовых столбцов отчёта."""
        return self.__numeric_columns

from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.warehouse_model import warehouse_model


class turnover_row_dto:
    """Строка ОСВ с доменными ссылками и именованными итогами движения."""

    def __init__(self, storage: warehouse_model, nomenclature: nomenclature_model,
                 range: range_model, opening_balance: float, income: float, expense: float) -> None:
        """Сохраняет измерения строки и рассчитанные прототипом суммы."""
        self.__storage = storage
        self.__nomenclature = nomenclature
        self.__range = range
        self.__opening_balance = opening_balance
        self.__income = income
        self.__expense = expense

    @property
    def storage(self) -> warehouse_model:
        """Склад, по которому собраны движения."""
        return self.__storage

    @property
    def nomenclature(self) -> nomenclature_model:
        """Товар, по которому собраны движения."""
        return self.__nomenclature

    @property
    def range(self) -> range_model:
        """Единица измерения всех количеств строки."""
        return self.__range

    @property
    def opening_balance(self) -> float:
        """Сальдо движений до начала периода."""
        return self.__opening_balance

    @property
    def income(self) -> float:
        """Сумма положительных движений в периоде."""
        return self.__income

    @property
    def expense(self) -> float:
        """Модуль суммы отрицательных движений в периоде."""
        return self.__expense

    @property
    def closing_balance(self) -> float:
        """Сальдо на конец периода с учётом прихода и расхода."""
        return self.opening_balance + self.income - self.expense

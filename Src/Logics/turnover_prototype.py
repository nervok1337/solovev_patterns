from collections.abc import Iterable
from datetime import date
from math import fsum

from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.turnover_row_dto import turnover_row_dto
from Src.Logics.prototype import prototype
from Src.Models.transaction_model import transaction_model


class turnover_prototype:
    """Рассчитывает начальные остатки и использует общий прототип для отбора движений."""

    def __init__(self, source: Iterable[transaction_model],
                 *, start: date | None = None, end: date | None = None) -> None:
        """Сохраняет исходный снимок и необязательные включённые границы периода."""
        if ((start is not None and type(start) is not date)
                or (end is not None and type(end) is not date)
                or (start is not None and end is not None and start > end)):
            raise ValueError("Период ОСВ должен содержать даты начала и окончания в верном порядке")
        self.__items = tuple(source)
        self.__start, self.__end = start, end

    def build(self, filters: list[filter_dto]) -> list[turnover_row_dto]:
        """Считает остатки до отбора, затем обороты по отфильтрованным данным периода."""
        source = tuple(item for item in self.__items
                       if self.__end is None or item.period.date() <= self.__end)
        history = {}
        for item in source:
            if self.__start is not None and item.period.date() < self.__start:
                history.setdefault(self.__key(item), []).append(item.value)
        opening = {key: fsum(values) for key, values in history.items()}

        selected = prototype(source, transaction_model).clone(filters)
        groups = {}
        for item in selected.data:
            groups.setdefault(self.__key(item), []).append(item)
        return [self.__build_row(items, opening.get(key, 0.0)) for key, items in groups.items()]

    @staticmethod
    def __key(item: transaction_model) -> tuple[str, str, str]:
        """Разделяет движения по складу, товару и единице измерения."""
        return item.storage.unique_code, item.nomenclature.unique_code, item.range.unique_code

    def __build_row(self, items: list[transaction_model], opening: float) -> turnover_row_dto:
        """Собирает именованные суммы одной группы без деталей формата HTTP."""
        first = items[0]
        period = [item for item in items
                  if self.__start is None or item.period.date() >= self.__start]
        income = fsum(item.value for item in period if item.value > 0)
        expense = fsum(-item.value for item in period if item.value < 0)
        return turnover_row_dto(first.storage, first.nomenclature, first.range,
                                opening_balance=opening, income=income, expense=expense)

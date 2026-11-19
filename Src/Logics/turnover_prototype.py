from collections.abc import Iterable
from datetime import date
from math import fsum

from Src.Dtos.turnover_row_dto import turnover_row_dto
from Src.Logics.prototype import prototype
from Src.Models.transaction_model import transaction_model


class turnover_prototype(prototype[transaction_model]):
    """Применяет общий clone к транзакциям и строит ОСВ по отобранным движениям."""

    def __init__(self, source: Iterable[transaction_model], model_type: type[transaction_model],
                 *, start: date, end: date) -> None:
        """Сохраняет период отчёта; при клонировании он переносится вместе с прототипом."""
        super().__init__(source, model_type)
        if type(start) is not date or type(end) is not date or start > end:
            raise ValueError("Период ОСВ должен содержать даты начала и окончания в верном порядке")
        self.__start, self.__end = start, end

    @property
    def rows(self) -> list[turnover_row_dto]:
        """Суммирует остатки и обороты без смешивания разных складов, товаров и единиц."""
        groups = {}
        for item in self._items:
            day = item.period.date()
            if day > self.__end:
                continue
            key = (item.storage.unique_code, item.nomenclature.unique_code, item.range.unique_code)
            groups.setdefault(key, []).append(item)
        return [self.__build_row(items) for items in groups.values()]

    def __build_row(self, items: list[transaction_model]) -> turnover_row_dto:
        """Собирает именованные суммы одной группы без деталей формата HTTP."""
        first = items[0]
        opening = fsum(item.value for item in items if item.period.date() < self.__start)
        period = [item for item in items if item.period.date() >= self.__start]
        income = fsum(item.value for item in period if item.value > 0)
        expense = fsum(-item.value for item in period if item.value < 0)
        return turnover_row_dto(first.storage, first.nomenclature, first.range,
                                opening_balance=opening, income=income, expense=expense)


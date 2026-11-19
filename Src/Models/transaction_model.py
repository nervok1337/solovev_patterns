from datetime import datetime
from math import isfinite

from Src.Core.entity_model import entity_model
from Src.Core.validator import validator
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.warehouse_model import warehouse_model


class transaction_model(entity_model):
    """Движение номенклатуры: положительное количество — приход, отрицательное — расход."""

    def __init__(self, nomenclature: nomenclature_model, storage: warehouse_model,
                 value: float, period: datetime, range: range_model | None = None) -> None:
        """Создаёт движение с явной единицей или единицей самой номенклатуры."""
        super().__init__()
        validator.validate(nomenclature, nomenclature_model)
        validator.validate(storage, warehouse_model)
        validator.validate(period, datetime)
        unit = nomenclature.range if range is None else range
        validator.validate(unit, range_model)
        self.__nomenclature = nomenclature
        self.__storage = storage
        self.__range = unit
        self.__period = period
        self.name = nomenclature.name
        self.value = value

    @property
    def nomenclature(self) -> nomenclature_model:
        """Возвращает номенклатуру движения."""
        return self.__nomenclature

    @property
    def storage(self) -> warehouse_model:
        """Возвращает склад движения."""
        return self.__storage

    @property
    def range(self) -> range_model:
        """Возвращает единицу количества движения."""
        return self.__range

    @property
    def period(self) -> datetime:
        """Возвращает дату и время движения в сохранённом часовом поясе."""
        return self.__period

    @property
    def value(self) -> float:
        """Возвращает количество со знаком движения."""
        return self.__value

    @value.setter
    def value(self, source: float) -> None:
        """Отклоняет ноль, логические и неограниченные числовые значения."""
        if isinstance(source, bool) or not isinstance(source, (int, float)):
            raise ValueError("Количество движения должно быть числом")
        try:
            value = float(source)
        except OverflowError as error:
            raise ValueError("Количество движения слишком велико") from error
        if value == 0 or not isfinite(value):
            raise ValueError("Количество движения должно быть конечным и ненулевым")
        self.__value = value

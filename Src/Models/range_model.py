from __future__ import annotations

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception


class range_model(entity_model):
    """Единица измерения с коэффициентом пересчёта."""

    __conversion_factor: float
    __base_range: range_model

    @classmethod
    def create(
        cls,
        name: str,
        conversion_factor: float,
        base_range: range_model | None = None,
    ) -> range_model:
        """Создаёт единицу измерения фабричным методом."""
        return cls(name, conversion_factor, base_range)

    def __init__(
        self,
        name: str,
        conversion_factor: float,
        base_range: range_model | None = None,
    ) -> None:
        """Создаёт базовую или производную единицу измерения."""
        super().__init__()
        self.name = name
        self.conversion_factor = conversion_factor

        if base_range is None and self.conversion_factor != 1:
            raise arguments_exception(
                "conversion_factor",
                "Коэффициент базовой единицы должен быть равен 1!",
            )

        self.base_range = self if base_range is None else base_range

    @property
    def conversion_factor(self) -> float:
        """Возвращает коэффициент пересчёта в базовую единицу."""
        return self.__conversion_factor

    @conversion_factor.setter
    def conversion_factor(self, value: float) -> None:
        """Устанавливает положительный коэффициент пересчёта."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise arguments_exception(
                "conversion_factor",
                "Коэффициент пересчёта должен быть числом!",
            )

        if value <= 0:
            raise arguments_exception(
                "conversion_factor",
                "Коэффициент пересчёта должен быть больше нуля!",
            )

        self.__conversion_factor = float(value)

    @property
    def base_range(self) -> range_model:
        """Возвращает базовую единицу измерения."""
        return self.__base_range

    @base_range.setter
    def base_range(self, value: range_model) -> None:
        """Устанавливает базовую единицу измерения."""
        if not isinstance(value, range_model):
            raise arguments_exception(
                "base_range",
                "Базовая единица должна быть моделью единицы измерения!",
            )

        self.__base_range = value

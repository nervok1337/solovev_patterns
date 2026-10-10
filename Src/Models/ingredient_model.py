from __future__ import annotations

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.nomenclature_model import nomenclature_model


class ingredient_model(entity_model):
    """Строка технологической карты с весом ингредиента."""

    __nomenclature: nomenclature_model
    __gross_weight: float
    __net_weight: float

    @classmethod
    def create(
        cls,
        nomenclature: nomenclature_model,
        gross_weight: float,
        net_weight: float,
    ) -> ingredient_model:
        """Создаёт ингредиент фабричным методом."""
        return cls(nomenclature, gross_weight, net_weight)

    def __init__(
        self,
        nomenclature: nomenclature_model,
        gross_weight: float,
        net_weight: float,
    ) -> None:
        """Создаёт строку рецепта для указанной номенклатуры."""
        super().__init__()
        self.nomenclature = nomenclature
        self.gross_weight = gross_weight
        self.net_weight = net_weight

    @staticmethod
    def __validate_weight(field: str, value: float, allow_zero: bool) -> float:
        """Проверяет числовой вес ингредиента."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise arguments_exception(field, "Вес должен быть числом!")

        if value < 0 or (value == 0 and not allow_zero):
            raise arguments_exception(field, "Вес указан некорректно!")

        return float(value)

    @property
    def nomenclature(self) -> nomenclature_model:
        """Возвращает номенклатуру ингредиента."""
        return self.__nomenclature

    @nomenclature.setter
    def nomenclature(self, value: nomenclature_model) -> None:
        """Устанавливает номенклатуру ингредиента."""
        if not isinstance(value, nomenclature_model):
            raise arguments_exception(
                "nomenclature",
                "Ингредиент должен ссылаться на номенклатуру!",
            )

        self.__nomenclature = value
        self.name = value.name

    @property
    def gross_weight(self) -> float:
        """Возвращает вес ингредиента брутто."""
        return self.__gross_weight

    @gross_weight.setter
    def gross_weight(self, value: float) -> None:
        """Устанавливает положительный вес ингредиента брутто."""
        gross_weight = self.__validate_weight("gross_weight", value, False)
        if hasattr(self, "_ingredient_model__net_weight"):
            if self.__net_weight > gross_weight:
                raise arguments_exception(
                    "gross_weight",
                    "Вес брутто не может быть меньше веса нетто!",
                )

        self.__gross_weight = gross_weight

    @property
    def net_weight(self) -> float:
        """Возвращает вес ингредиента нетто."""
        return self.__net_weight

    @net_weight.setter
    def net_weight(self, value: float) -> None:
        """Устанавливает неотрицательный вес ингредиента нетто."""
        net_weight = self.__validate_weight("net_weight", value, True)
        if net_weight > self.__gross_weight:
            raise arguments_exception(
                "net_weight",
                "Вес нетто не может превышать вес брутто!",
            )

        self.__net_weight = net_weight

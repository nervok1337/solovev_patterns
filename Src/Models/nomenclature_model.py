from __future__ import annotations

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.range_model import range_model


class nomenclature_model(entity_model):
    """Учётная единица продукции, входящая в группу номенклатуры."""

    __full_name: str
    __group: nomenclature_group_model
    __range: range_model

    @classmethod
    def create(
        cls,
        name: str,
        full_name: str,
        group: nomenclature_group_model,
        range: range_model,
    ) -> nomenclature_model:
        """Создаёт элемент номенклатуры фабричным методом."""
        return cls(name, full_name, group, range)

    def __init__(
        self,
        name: str,
        full_name: str,
        group: nomenclature_group_model,
        range: range_model,
    ) -> None:
        """Создаёт номенклатуру с группой и единицей измерения."""
        super().__init__()
        self.name = name
        self.full_name = full_name
        self.group = group
        self.range = range

    @property
    def full_name(self) -> str:
        """Возвращает полное наименование номенклатуры."""
        return self.__full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        """Устанавливает полное наименование длиной до 255 символов."""
        if not isinstance(value, str) or value.strip() == "":
            raise arguments_exception(
                "full_name",
                "Полное наименование не может быть пустым!",
            )

        if len(value.strip()) > 255:
            raise arguments_exception(
                "full_name",
                "Длина полного наименования не может превышать 255 символов!",
            )

        self.__full_name = value.strip()

    @property
    def group(self) -> nomenclature_group_model:
        """Возвращает группу номенклатуры."""
        return self.__group

    @group.setter
    def group(self, value: nomenclature_group_model) -> None:
        """Устанавливает группу номенклатуры."""
        if not isinstance(value, nomenclature_group_model):
            raise arguments_exception(
                "group",
                "Группа должна быть моделью группы номенклатуры!",
            )

        self.__group = value

    @property
    def range(self) -> range_model:
        """Возвращает единицу измерения номенклатуры."""
        return self.__range

    @range.setter
    def range(self, value: range_model) -> None:
        """Устанавливает единицу измерения номенклатуры."""
        if not isinstance(value, range_model):
            raise arguments_exception(
                "range",
                "Единица должна быть моделью единицы измерения!",
            )

        self.__range = value

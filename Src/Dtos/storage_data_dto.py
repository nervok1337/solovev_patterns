from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.warehouse_model import warehouse_model


class storage_data_dto:
    """Восстановленные коллекции моделей без изменения действующего хранилища."""

    def __init__(self, ranges: list[range_model],
                 groups: list[nomenclature_group_model],
                 warehouses: list[warehouse_model],
                 nomenclatures: list[nomenclature_model],
                 recipes: list[recipe_model], is_loaded: bool):
        """Сохраняет восстановленные коллекции и признак формирования первичных данных."""
        self.__ranges = ranges
        self.__groups = groups
        self.__warehouses = warehouses
        self.__nomenclatures = nomenclatures
        self.__recipes = recipes
        self.__is_loaded = is_loaded

    @property
    def ranges(self) -> list[range_model]:
        """Возвращает копию списка восстановленных единиц измерения."""
        return self.__ranges.copy()

    @property
    def groups(self) -> list[nomenclature_group_model]:
        """Возвращает копию списка восстановленных групп номенклатуры."""
        return self.__groups.copy()

    @property
    def warehouses(self) -> list[warehouse_model]:
        """Возвращает копию списка восстановленных складов."""
        return self.__warehouses.copy()

    @property
    def nomenclatures(self) -> list[nomenclature_model]:
        """Возвращает копию списка восстановленных номенклатур."""
        return self.__nomenclatures.copy()

    @property
    def recipes(self) -> list[recipe_model]:
        """Возвращает копию списка восстановленных рецептов."""
        return self.__recipes.copy()

    @property
    def is_loaded(self) -> bool:
        """Возвращает сохранённый признак формирования первичных данных."""
        return self.__is_loaded

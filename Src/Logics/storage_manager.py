from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import validator
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.warehouse_model import warehouse_model


class storage_manager(abstract_manager):
    """Хранит уникальные доменные объекты в едином экземпляре."""

    def __new__(cls):
        """Возвращает единственный экземпляр менеджера хранилища."""
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        """Создаёт независимые коллекции при первом создании singleton."""
        if getattr(self, "_storage_manager__initialized", False):
            return

        self.__ranges: dict[str, range_model] = {}
        self.__groups: dict[str, nomenclature_group_model] = {}
        self.__warehouses: dict[str, warehouse_model] = {}
        self.__nomenclatures: dict[str, nomenclature_model] = {}
        self.__recipes: dict[str, recipe_model] = {}
        self.__is_loaded = False
        self.__initialized = True

    @property
    def is_loaded(self) -> bool:
        """Возвращает признак формирования первичных данных."""
        return self.__is_loaded

    def convert(self, settings: settings_model) -> bool:
        """Формирует первичные данные приложения при первом старте."""
        validator.validate(settings, settings_model)

        if not settings.is_first_start:
            return False

        if self.__is_loaded:
            return True

        piece = range_model.create("Штука", 1)
        kilogram = range_model.create("Килограмм", 1)
        gram = range_model.create("Грамм", 0.001, kilogram)
        liter = range_model.create("Литр", 1)
        milliliter = range_model.create("Миллилитр", 0.001, liter)

        products = nomenclature_group_model.create("Продукты")
        drinks = nomenclature_group_model.create("Напитки")
        packaging = nomenclature_group_model.create("Упаковка")

        main_warehouse = warehouse_model.create("Основной склад")
        kitchen = warehouse_model.create("Кухня")
        bar = warehouse_model.create("Бар")

        for unit in (piece, kilogram, gram, liter, milliliter):
            self.add_range(unit)

        for group in (products, drinks, packaging):
            self.add_group(group)

        for warehouse in (main_warehouse, kitchen, bar):
            self.add_warehouse(warehouse)

        water = nomenclature_model.create(
            "Вода",
            "Вода питьевая",
            drinks,
            liter,
        )
        milk = nomenclature_model.create(
            "Молоко",
            "Молоко питьевое",
            products,
            liter,
        )
        sugar = nomenclature_model.create(
            "Сахар",
            "Сахар-песок",
            products,
            kilogram,
        )
        package = nomenclature_model.create(
            "Пакет",
            "Пакет упаковочный",
            packaging,
            piece,
        )
        initial_nomenclatures = (water, milk, sugar, package)
        for nomenclature in initial_nomenclatures:
            self.add_nomenclature(nomenclature)

        milk_caramel = recipe_model.create(
            "Молочная карамель",
            (
                ingredient_model.create(sugar, 200, 200),
                ingredient_model.create(milk, 250, 250),
                ingredient_model.create(water, 50, 50),
                ingredient_model.create(package, 10, 0),
            ),
        )
        self.add_recipe(milk_caramel)

        self.__is_loaded = True
        return True

    def add_range(self, value: range_model) -> None:
        """Добавляет единицу измерения, не дублируя её идентификатор."""
        validator.validate(value, range_model)
        self.__ranges.setdefault(value.id, value)

    def add_group(self, value: nomenclature_group_model) -> None:
        """Добавляет группу, не дублируя её идентификатор."""
        validator.validate(value, nomenclature_group_model)
        self.__groups.setdefault(value.id, value)

    def add_warehouse(self, value: warehouse_model) -> None:
        """Добавляет склад, не дублируя его идентификатор."""
        validator.validate(value, warehouse_model)
        self.__warehouses.setdefault(value.id, value)

    def add_nomenclature(self, value: nomenclature_model) -> None:
        """Добавляет номенклатуру, не дублируя её идентификатор."""
        validator.validate(value, nomenclature_model)
        self.__nomenclatures.setdefault(value.id, value)

    def add_recipe(self, value: recipe_model) -> None:
        """Добавляет технологическую карту без дублирования."""
        validator.validate(value, recipe_model)
        self.__recipes.setdefault(value.id, value)

    @property
    def ranges(self) -> list[range_model]:
        """Возвращает список единиц измерения."""
        return list(self.__ranges.values())

    @property
    def groups(self) -> list[nomenclature_group_model]:
        """Возвращает список групп номенклатуры."""
        return list(self.__groups.values())

    @property
    def warehouses(self) -> list[warehouse_model]:
        """Возвращает список складов."""
        return list(self.__warehouses.values())

    @property
    def nomenclatures(self) -> list[nomenclature_model]:
        """Возвращает список номенклатуры."""
        return list(self.__nomenclatures.values())

    @property
    def recipes(self) -> list[recipe_model]:
        """Возвращает список технологических карт."""
        return list(self.__recipes.values())

from contextlib import contextmanager
from copy import deepcopy
from threading import RLock
from typing import get_args

from Src.Core.abstract_storage import abstract_storage
from Src.Core.entity_model import entity_model
from Src.Core.validator import operation_exception
from Src.Core.abstract_manager import abstract_manager
from Src.Core.common import common
from Src.Core.validator import validator
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.settings_model import settings_model
from Src.Models.warehouse_model import warehouse_model


class storage_manager(abstract_manager, abstract_storage):
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
        self.__additional = {}
        self.__lock = RLock()
        self.__initialized = True

    @property
    def is_loaded(self) -> bool:
        """Возвращает признак формирования первичных данных."""
        return self.__is_loaded

    def convert(self, settings: settings_model) -> bool:
        """Формирует первичные данные приложения при первом старте."""
        validator.validate(settings, settings_model)

        self.__index(settings)

        if not settings.is_first_start:
            return False

        if self.__is_loaded:
            return True

        piece = range_model.create("Штука", 1)
        gram = range_model.create("Грамм", 1)
        kilogram = range_model.create("Килограмм", 1000, gram)
        milliliter = range_model.create("Миллилитр", 1)
        liter = range_model.create("Литр", 1000, milliliter)

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

        caramel_base = recipe_model.create(
            "Карамельная основа",
            (
                ingredient_model.create(sugar, 200, 200),
                ingredient_model.create(milk, 250, 250),
                ingredient_model.create(water, 50, 50),
            ),
        )
        milk_caramel = recipe_model.create(
            "Молочная карамель",
            (
                caramel_base,
                ingredient_model.create(package, 10, 0),
            ),
        )
        self.add_recipe(milk_caramel)

        self.__is_loaded = True
        self.__index(list(self.__collections().values()))
        return True

    def add_range(self, value: range_model) -> None:
        """Добавляет единицу измерения, не дублируя её идентификатор."""
        validator.validate(value, range_model)
        self.__ranges.setdefault(value.unique_code, value)

    def add_group(self, value: nomenclature_group_model) -> None:
        """Добавляет группу, не дублируя её идентификатор."""
        validator.validate(value, nomenclature_group_model)
        self.__groups.setdefault(value.unique_code, value)

    def add_warehouse(self, value: warehouse_model) -> None:
        """Добавляет склад, не дублируя его идентификатор."""
        validator.validate(value, warehouse_model)
        self.__warehouses.setdefault(value.unique_code, value)

    def add_nomenclature(self, value: nomenclature_model) -> None:
        """Добавляет номенклатуру, не дублируя её идентификатор."""
        validator.validate(value, nomenclature_model)
        self.__nomenclatures.setdefault(value.unique_code, value)

    def add_recipe(self, value: recipe_model) -> None:
        """Добавляет технологическую карту без дублирования."""
        validator.validate(value, recipe_model)
        self.__recipes.setdefault(value.unique_code, value)

    def entity_types(self) -> list[str]:
        """Находит публичные коллекции хранилища через общую рефлексию."""
        return [
            field for field in common.get_fields(self)
            if common.is_collection(getattr(self, field))
        ]

    def find_entity(self, entity_type: str, entity_code: str):
        """Находит сущность в коллекции по типу и уникальному коду."""
        type_aliases = {
            "nomenclature": "nomenclatures",
            "номенклатура": "nomenclatures",
            "range": "ranges",
            "unit": "ranges",
            "unit_of_measurement": "ranges",
            "единица измерения": "ranges",
            "recipe": "recipes",
            "рецепт": "recipes",
            "group": "groups",
            "warehouse": "warehouses",
        }
        collection_name = type_aliases.get(entity_type, entity_type)
        try:
            return self.get_entity(collection_name, entity_code), None, None
        except ValueError:
            return None, f"Неподдерживаемый тип: {entity_type}", 400
        except KeyError:
            return None, f"Сущность с кодом {entity_code} не найдена", 404

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

    def model_types(self) -> dict[str, type[entity_model]]:
        """Определяет типы коллекций и вложенных сущностей по аннотациям."""
        result = {}

        def entities_in(annotation):
            """Извлекает классы сущностей из составной аннотации."""
            if isinstance(annotation, type) and issubclass(annotation, entity_model):
                yield annotation
            for argument in get_args(annotation):
                yield from entities_in(argument)

        pending = [type(self), settings_model]
        visited = set()
        while pending:
            model_type = pending.pop(0)
            if model_type in visited:
                continue
            visited.add(model_type)
            for name, annotation in common.get_annotations(model_type).items():
                for related in entities_in(annotation):
                    if related in result.values():
                        continue
                    if name in result:
                        raise ValueError(f"Неоднозначная коллекция {name}")
                    result[name] = related
                    pending.append(related)
        return result

    def __collections(self):
        """Предоставляет собственные словари через имена публичных коллекций."""
        return {name: getattr(self, f"_{__class__.__name__}__{name}")
                for name in self.entity_types()}

    def __index(self, source):
        """Индексирует вложенные модели, сохраняя прежний формат публичной выгрузки."""
        types = self.model_types()
        roots = self.__collections()
        for item in common.walk(source):
            if not isinstance(item, entity_model):
                continue
            name = next(name for name, model_type in types.items() if type(item) is model_type)
            if item.unique_code not in roots.get(name, {}):
                self.__additional.setdefault(name, {}).setdefault(item.unique_code, item)

    def entities(self, collection: str) -> list[entity_model]:
        """Возвращает корневые и вложенные сущности указанного типа."""
        if collection not in self.model_types():
            raise ValueError(f"Неизвестная коллекция: {collection}")
        values = self.__additional.get(collection, {}).copy()
        values.update(self.__collections().get(collection, {}))
        return list(values.values())

    def get_entity(self, collection: str, code: str) -> entity_model:
        """Находит объект без привязки результата к HTTP."""
        for entity in self.entities(collection):
            if entity.unique_code == code:
                return entity
        raise KeyError(f"Сущность {collection}/{code} не найдена")

    def save_entity(self, collection: str, entity: entity_model) -> None:
        """Сохраняет сущность, проверяя тип и уникальность кода."""
        types = self.model_types()
        if collection not in types or type(entity) is not types[collection]:
            raise ValueError("Неверный тип коллекции или сущности")
        if any(item.unique_code == entity.unique_code for name in types for item in self.entities(name)):
            raise operation_exception("Код сущности уже занят")
        entity.validate()
        target = self.__collections().get(collection)
        if target is None:
            target = self.__additional.setdefault(collection, {})
        target[entity.unique_code] = entity
        self.__index(entity)

    def delete_entity(self, collection: str, code: str) -> None:
        """Удаляет объект из принадлежащего менеджеру словаря."""
        self.get_entity(collection, code)
        for values in (self.__collections().get(collection, {}), self.__additional.get(collection, {})):
            values.pop(code, None)

    @contextmanager
    def transaction(self):
        """Изолирует операцию и фиксирует общий граф только при успехе."""
        with self.__lock:
            staged = object.__new__(type(self))
            staged.__dict__ = deepcopy(vars(self), {id(self.__lock): self.__lock})
            yield staged
            self.__dict__ = staged.__dict__

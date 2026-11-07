from math import isfinite

from Src.Core.abstract_deserializer import (
    abstract_deserialize_factory,
    abstract_model_deserializer,
    restore_model,
)
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.organization_model import organization_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.warehouse_model import warehouse_model


def number(source: dict, field: str) -> float:
    """Проверить числовое поле до передачи в конструктор модели."""
    value = source[field]
    if type(value) not in (int, float) or not isfinite(value):
        raise arguments_exception(field, "Ожидается конечное число!")
    return value


class named_deserializer(abstract_model_deserializer):
    """Восстанавливает группу или склад, содержащие только код и имя."""

    fields = {"unique_code", "name"}

    def __init__(self, model_type: type[entity_model]):
        self.__model_type = model_type

    def restore(self, source: dict, restore: restore_model) -> entity_model:
        return self.__model_type.create(source["name"])


class range_deserializer(abstract_model_deserializer):
    fields = {"unique_code", "name", "conversion_factor", "base_range"}

    def restore(self, source: dict, restore: restore_model) -> range_model:
        base = source["base_range"]
        if base is not None:
            base = restore(base, range_model)
        # Для базовой единицы конструктор сам восстанавливает самоссылку.
        return range_model.create(
            source["name"], number(source, "conversion_factor"), base
        )


class nomenclature_deserializer(abstract_model_deserializer):
    fields = {"unique_code", "name", "full_name", "group", "range"}

    def restore(self, source: dict, restore: restore_model) -> nomenclature_model:
        return nomenclature_model.create(
            source["name"], source["full_name"],
            restore(source["group"], nomenclature_group_model),
            restore(source["range"], range_model),
        )


class ingredient_deserializer(abstract_model_deserializer):
    fields = {"unique_code", "name", "nomenclature", "gross_weight", "net_weight"}

    def restore(self, source: dict, restore: restore_model) -> ingredient_model:
        model = ingredient_model.create(
            restore(source["nomenclature"], nomenclature_model),
            number(source, "gross_weight"), number(source, "net_weight"),
        )
        model.name = source["name"]
        return model


class recipe_deserializer(abstract_model_deserializer):
    fields = {"unique_code", "name", "ingredients", "gross_weight", "net_weight"}

    def restore(self, source: dict, restore: restore_model) -> recipe_model:
        items = source["ingredients"]
        if not isinstance(items, list):
            raise arguments_exception("ingredients", "Ожидается список!")
        ingredients = []
        for item in items:
            if not isinstance(item, dict):
                raise arguments_exception("ingredients", "Ожидается объект!")
            # В существующем формате вложенная карта отличается полем ingredients.
            model_type = recipe_model if "ingredients" in item else ingredient_model
            ingredients.append(restore(item, model_type))
        model = recipe_model.create(source["name"], ingredients)
        for field in ("gross_weight", "net_weight"):
            if number(source, field) != getattr(model, field):
                raise arguments_exception(field, "Вес рецепта не совпадает с его составом!")
        return model


class organization_deserializer(abstract_model_deserializer):
    fields = {"unique_code", "name", "inn", "bik", "account", "ownership_form"}

    def restore(self, source: dict, restore: restore_model) -> organization_model:
        return organization_model(
            source["name"], source["inn"], source["bik"],
            source["account"], source["ownership_form"],
        )


class deserialize_factory(abstract_deserialize_factory):
    """Создаёт обработчик; восстановление данных выполняет сам обработчик."""

    def __init__(self):
        self.__mapping = {
            range_model: range_deserializer,
            nomenclature_model: nomenclature_deserializer,
            ingredient_model: ingredient_deserializer,
            recipe_model: recipe_deserializer,
            organization_model: organization_deserializer,
        }

    def create(self, model_type: type[entity_model]) -> abstract_model_deserializer:
        if model_type in (nomenclature_group_model, warehouse_model):
            return named_deserializer(model_type)
        handler = self.__mapping.get(model_type)
        if handler is None:
            raise arguments_exception("model_type", "Тип модели не поддерживается!")
        return handler()

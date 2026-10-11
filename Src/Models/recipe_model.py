from __future__ import annotations

from collections.abc import Iterable

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.ingredient_model import ingredient_model


class recipe_model(entity_model):
    """Технологическая карта с набором ингредиентов."""

    @classmethod
    def create(
        cls,
        name: str,
        ingredients: Iterable[ingredient_model | recipe_model] | None = None,
    ) -> recipe_model:
        """Создаёт технологическую карту фабричным методом."""
        return cls(name, ingredients)

    def __init__(
        self,
        name: str,
        ingredients: Iterable[ingredient_model | recipe_model] | None = None,
    ) -> None:
        """Создаёт рецепт и добавляет переданные строки ингредиентов."""
        super().__init__()
        self.name = name
        self.__ingredients: list[ingredient_model | recipe_model] = []

        if ingredients is not None:
            for ingredient in ingredients:
                self.add_ingredient(ingredient)

    def add_ingredient(self, value: ingredient_model | recipe_model) -> None:
        """Добавляет в рецепт ингредиент или вложенную карту."""
        self.__validate_ingredient(value)
        if isinstance(value, recipe_model) and value.__contains_recipe(self):
            raise arguments_exception(
                "ingredient",
                "Технологические карты не могут образовывать цикл!",
            )

        if value not in self.__ingredients:
            self.__ingredients.append(value)

    def remove_ingredient(self, value: ingredient_model | recipe_model) -> None:
        """Исключает ингредиент или вложенную карту из рецепта."""
        self.__validate_ingredient(value)
        if value in self.__ingredients:
            self.__ingredients.remove(value)

    @staticmethod
    def __validate_ingredient(
        value: ingredient_model | recipe_model,
    ) -> None:
        """Проверяет тип элемента технологической карты."""
        if not isinstance(value, (ingredient_model, recipe_model)):
            raise arguments_exception(
                "ingredient",
                "В рецепт можно добавить ингредиент или другую карту!",
            )

    def __contains_recipe(self, value: recipe_model) -> bool:
        """Рекурсивно проверяет наличие карты в составе рецепта."""
        if self is value:
            return True

        return any(
            item.__contains_recipe(value)
            for item in self.__ingredients
            if isinstance(item, recipe_model)
        )

    def __calculate_weight(self, gross: bool) -> float:
        """Рекурсивно вычисляет вес составной технологической карты."""
        result = 0.0
        for item in self.__ingredients:
            if isinstance(item, recipe_model):
                result += item.__calculate_weight(gross)
            elif gross:
                result += item.gross_weight
            else:
                result += item.net_weight

        return result

    @property
    def ingredients(self) -> list[ingredient_model | recipe_model]:
        """Возвращает копию состава технологической карты."""
        return list(self.__ingredients)

    @property
    def gross_weight(self) -> float:
        """Рекурсивно вычисляет общий вес брутто."""
        return self.__calculate_weight(True)

    @property
    def net_weight(self) -> float:
        """Рекурсивно вычисляет общий вес нетто."""
        return self.__calculate_weight(False)

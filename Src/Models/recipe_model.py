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
        ingredients: Iterable[ingredient_model] | None = None,
    ) -> recipe_model:
        """Создаёт технологическую карту фабричным методом."""
        return cls(name, ingredients)

    def __init__(
        self,
        name: str,
        ingredients: Iterable[ingredient_model] | None = None,
    ) -> None:
        """Создаёт рецепт и добавляет переданные строки ингредиентов."""
        super().__init__()
        self.name = name
        self.__ingredients: list[ingredient_model] = []

        if ingredients is not None:
            for ingredient in ingredients:
                self.add_ingredient(ingredient)

    def add_ingredient(self, value: ingredient_model) -> None:
        """Добавляет в рецепт уникальную строку ингредиента."""
        self.__validate_ingredient(value)
        if value not in self.__ingredients:
            self.__ingredients.append(value)

    def remove_ingredient(self, value: ingredient_model) -> None:
        """Исключает строку ингредиента из рецепта."""
        self.__validate_ingredient(value)
        if value in self.__ingredients:
            self.__ingredients.remove(value)

    @staticmethod
    def __validate_ingredient(value: ingredient_model) -> None:
        """Проверяет тип строки ингредиента."""
        if not isinstance(value, ingredient_model):
            raise arguments_exception(
                "ingredient",
                "В рецепт можно добавить только ингредиент!",
            )

    @property
    def ingredients(self) -> list[ingredient_model]:
        """Возвращает копию списка ингредиентов рецепта."""
        return list(self.__ingredients)

    @property
    def gross_weight(self) -> float:
        """Вычисляет общий вес брутто всех ингредиентов."""
        return sum(item.gross_weight for item in self.__ingredients)

    @property
    def net_weight(self) -> float:
        """Вычисляет общий вес нетто всех ингредиентов."""
        return sum(item.net_weight for item in self.__ingredients)

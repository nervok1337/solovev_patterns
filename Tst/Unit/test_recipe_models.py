import pytest

from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Models.ingredient_model import ingredient_model
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model


@pytest.fixture
def product_group() -> nomenclature_group_model:
    """Создаёт группу продуктов для тестов рецепта."""
    return nomenclature_group_model.create("Продукты")


@pytest.fixture
def gram() -> range_model:
    """Создаёт единицу веса для тестов рецепта."""
    return range_model.create("Грамм", 1)


def create_ingredient(
    name: str,
    gross_weight: float,
    net_weight: float,
    group: nomenclature_group_model,
    unit: range_model,
) -> ingredient_model:
    """Создаёт тестовую строку ингредиента через фабричные методы."""
    nomenclature = nomenclature_model.create(name, name, group, unit)
    return ingredient_model.create(nomenclature, gross_weight, net_weight)


def test_models_recipe_and_ingredient_inherit_entity_model(
    product_group,
    gram,
):
    """Проверяет общий базовый тип новых доменных моделей."""
    ingredient = create_ingredient("Сахар", 200, 190, product_group, gram)
    recipe = recipe_model.create("Карамель", (ingredient,))

    assert isinstance(ingredient, entity_model)
    assert isinstance(recipe, entity_model)


def test_equals_recipe_model_weights_from_ingredients(product_group, gram):
    """Проверяет сумму весов брутто и нетто всех ингредиентов."""
    sugar = create_ingredient("Сахар", 200, 190, product_group, gram)
    milk = create_ingredient("Молоко", 250, 240, product_group, gram)

    recipe = recipe_model.create("Карамель", (sugar, milk))

    assert recipe.gross_weight == 450
    assert recipe.net_weight == 430


def test_increased_recipe_model_weights_after_add_ingredient(
    product_group,
    gram,
):
    """Проверяет пересчёт весов после добавления ингредиента."""
    sugar = create_ingredient("Сахар", 200, 190, product_group, gram)
    milk = create_ingredient("Молоко", 250, 240, product_group, gram)
    recipe = recipe_model.create("Карамель", (sugar,))

    recipe.add_ingredient(milk)

    assert recipe.gross_weight == 450
    assert recipe.net_weight == 430


def test_decreased_recipe_model_weights_after_remove_ingredient(
    product_group,
    gram,
):
    """Проверяет пересчёт весов после исключения ингредиента."""
    sugar = create_ingredient("Сахар", 200, 190, product_group, gram)
    milk = create_ingredient("Молоко", 250, 240, product_group, gram)
    recipe = recipe_model.create("Карамель", (sugar, milk))

    recipe.remove_ingredient(milk)

    assert recipe.ingredients == [sugar]
    assert recipe.gross_weight == 200
    assert recipe.net_weight == 190


@pytest.mark.parametrize(
    ("gross_weight", "net_weight"),
    [(0, 0), (-1, 0), (10, -1), (10, 11), (True, 1), ("10", 1)],
)
def test_arguments_exception_ingredient_model_invalid_weights(
    product_group,
    gram,
    gross_weight,
    net_weight,
):
    """Проверяет отклонение некорректных весов ингредиента."""
    nomenclature = nomenclature_model.create(
        "Продукт",
        "Тестовый продукт",
        product_group,
        gram,
    )

    with pytest.raises(arguments_exception):
        ingredient_model.create(nomenclature, gross_weight, net_weight)

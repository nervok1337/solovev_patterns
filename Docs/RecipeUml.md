# UML-диаграмма моделей рецепта

```mermaid
classDiagram
    class entity_model {
        +id str
        +name str
    }

    class nomenclature_model {
        +full_name str
        +group nomenclature_group_model
        +range range_model
        +create(name, full_name, group, range) nomenclature_model
    }

    class ingredient_model {
        +nomenclature nomenclature_model
        +gross_weight float
        +net_weight float
        +create(nomenclature, gross_weight, net_weight) ingredient_model
    }

    class recipe_model {
        -ingredients list
        +gross_weight float
        +net_weight float
        +create(name, ingredients) recipe_model
        +add_ingredient(value) None
        +remove_ingredient(value) None
    }

    entity_model <|-- ingredient_model
    entity_model <|-- recipe_model
    ingredient_model --> nomenclature_model
    recipe_model *-- ingredient_model
```

`recipe_model` вычисляет веса брутто и нетто при обращении к свойствам,
складывая соответствующие веса всех строк. Поэтому добавление или исключение
ингредиента сразу отражается на итогах технологической карты.

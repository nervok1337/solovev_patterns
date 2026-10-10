# UML-диаграммы менеджеров

## Менеджер настроек

```mermaid
classDiagram
    class abstract_manager {
        <<abstract>>
        +convert(data) bool
        +is_loaded bool
    }

    class settings_manager {
        -instance: settings_manager
        -settings: settings_model
        -is_loaded: bool
        +convert(data: dict) bool
        +settings settings_model
        +is_loaded bool
    }

    class settings_model {
        +organization organization_model
        +boss_name str
        +account_name str
        +is_first_start bool
    }

    class organization_model {
        +name str
        +inn str
        +bik str
        +account str
        +ownership_form str
    }

    abstract_manager <|-- settings_manager
    settings_manager --> settings_model : creates
    settings_model *-- organization_model
```

`settings_manager` реализует шаблон Singleton: все вызовы конструктора
возвращают один экземпляр, а повторный вызов `__init__` не сбрасывает данные.

## Менеджер хранилища

```mermaid
classDiagram
    class abstract_manager {
        <<abstract>>
        +convert() bool
        +is_loaded bool
    }

    class storage_manager {
        -instance: storage_manager
        -ranges: dict
        -groups: dict
        -warehouses: dict
        -nomenclatures: dict
        -recipes: dict
        -is_loaded: bool
        +convert(settings: settings_model) bool
        +add_range(value: range_model) None
        +add_group(value: nomenclature_group_model) None
        +add_warehouse(value: warehouse_model) None
        +add_nomenclature(value: nomenclature_model) None
        +add_recipe(value: recipe_model) None
        +ranges list
        +groups list
        +warehouses list
        +nomenclatures list
        +recipes list
        +is_loaded bool
    }

    abstract_manager <|-- storage_manager
    storage_manager o-- range_model
    storage_manager o-- nomenclature_group_model
    storage_manager o-- warehouse_model
    storage_manager o-- nomenclature_model
    storage_manager o-- recipe_model
    nomenclature_model --> range_model
    nomenclature_model --> nomenclature_group_model
    storage_manager ..> settings_model : first start
```

Коллекции реализованы словарями с идентификаторами моделей в качестве ключей.
Это сохраняет уникальность объектов и делает повторное добавление идемпотентным.

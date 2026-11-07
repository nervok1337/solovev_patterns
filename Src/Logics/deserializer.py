from Src.Core.abstract_deserializer import abstract_deserialize_factory
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Dtos.storage_data_dto import storage_data_dto
from Src.Models.nomenclature_group_model import nomenclature_group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.recipe_model import recipe_model
from Src.Models.warehouse_model import warehouse_model


class _restore_context:
    """Общий контекст одной загрузки: идентичность объектов и контроль рекурсии."""

    def __init__(self, factory: abstract_deserialize_factory):
        self.__factory = factory
        self.__models: dict[str, entity_model] = {}
        self.__definitions: dict[str, dict] = {}
        self.__active: set[str] = set()

    def restore(self, source: dict, model_type: type[entity_model]) -> entity_model:
        if not isinstance(source, dict):
            raise arguments_exception("source", "Ожидается словарь модели!")
        handler = self.__factory.create(model_type)
        if set(source) != handler.fields:
            raise arguments_exception("source", f"Неверный набор полей {model_type.__name__}!")
        code = source["unique_code"]
        if not isinstance(code, str) or not code.strip():
            raise arguments_exception("unique_code", "Код должен быть непустой строкой!")
        if code != code.strip():
            raise arguments_exception("unique_code", "Код не должен содержать пробелы по краям!")
        if code in self.__active:
            raise arguments_exception("unique_code", "Обнаружена циклическая ссылка!")
        if code in self.__models:
            model = self.__models[code]
            if type(model) is not model_type or self.__definitions[code] != source:
                raise arguments_exception("unique_code", f"Противоречивые данные для кода {code}!")
            return model

        self.__active.add(code)
        try:
            model = handler.restore(source, self.restore)
            model.unique_code = code
            self.__models[code] = model
            self.__definitions[code] = source
            return model
        finally:
            self.__active.remove(code)


class deserializer:
    """Восстанавливает граф моделей; не читает файлы и не зависит от HTTP/JSON."""

    def __init__(self, factory: abstract_deserialize_factory):
        self.__factory = factory
        self.__sections = {
            "ranges": range_model,
            "groups": nomenclature_group_model,
            "warehouses": warehouse_model,
            "nomenclatures": nomenclature_model,
            "recipes": recipe_model,
        }

    def deserialize(self, source: dict, model_type: type[entity_model]) -> entity_model:
        """Восстановить отдельную сущность и все её вложения."""
        return _restore_context(self.__factory).restore(source, model_type)

    def deserialize_storage(self, source: dict) -> storage_data_dto:
        """Восстановить все разделы с общим контекстом ссылок для одной загрузки."""
        if not isinstance(source, dict) or set(source) != set(self.__sections) | {"is_loaded"}:
            raise arguments_exception("source", "Неверный набор разделов хранилища!")
        if type(source["is_loaded"]) is not bool:
            raise arguments_exception("is_loaded", "Ожидается логическое значение!")
        context = _restore_context(self.__factory)
        sections = {}
        for section, model_type in self.__sections.items():
            items = source[section]
            if not isinstance(items, list):
                raise arguments_exception(section, "Ожидается список моделей!")
            models = []
            codes = set()
            for item in items:
                model = context.restore(item, model_type)
                if model.unique_code in codes:
                    raise arguments_exception(section, "Повторный код в коллекции!")
                codes.add(model.unique_code)
                models.append(model)
            sections[section] = models
        return storage_data_dto(**sections, is_loaded=source["is_loaded"])

from typing import Any

from Src.Core.abstract_deserializer import abstract_deserialize_factory
from Src.Core.entity_model import entity_model
from Src.Core.exception import arguments_exception
from Src.Dtos.storage_data_dto import storage_data_dto


class _restore_context:
    """Один проход восстановления, общие экземпляры сущностей и контроль циклов."""

    def __init__(self, factory: abstract_deserialize_factory):
        self.__factory = factory
        self.__models: list[entity_model] = []
        self.__definitions: list[dict] = []
        self.__active: set[tuple[int, Any]] = set()

    def restore(self, source: object, model_type: Any) -> object:
        key = (id(source), model_type)
        if key in self.__active:
            raise arguments_exception("source", "Обнаружена циклическая ссылка!")
        self.__active.add(key)
        try:
            handler = self.__factory.create(model_type)
            model = handler.restore(source, self.restore)
            # Сущности имеют контракт равенства по идентичности. DTO этого не требуют.
            if isinstance(model, entity_model):
                for index, existing in enumerate(self.__models):
                    if existing == model:
                        if type(existing) is not type(model) or self.__definitions[index] != source:
                            raise arguments_exception("source", "Противоречивые данные одной сущности!")
                        return existing
                self.__models.append(model)
                self.__definitions.append(source)
            return model
        finally:
            self.__active.remove(key)


class deserializer:
    """Восстанавливает значения через абстрактную фабрику, без файлов и JSON."""

    def __init__(self, factory: abstract_deserialize_factory):
        self.__factory = factory

    def deserialize(self, source: object, model_type: Any) -> object:
        return _restore_context(self.__factory).restore(source, model_type)

    def deserialize_storage(self, source: dict) -> storage_data_dto:
        """Совместимый вход для снимка хранилища; поля берутся из DTO рефлексией."""
        return self.deserialize(source, storage_data_dto)

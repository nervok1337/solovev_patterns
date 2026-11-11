from typing import Any

from Src.Core.abstract_deserialize_factory import abstract_deserialize_factory
from Src.Dtos.storage_data_dto import storage_data_dto
from Src.Logics._restore_context import _restore_context


class deserializer:
    """Восстанавливает значения через абстрактную фабрику, без файлов и JSON."""

    def __init__(self, factory: abstract_deserialize_factory):
        """Принимает фабрику обработчиков через абстрактный контракт."""
        self.__factory = factory

    def deserialize(self, source: object, model_type: Any) -> object:
        """Восстанавливает значение и его вложения в независимом контексте загрузки."""
        return _restore_context(self.__factory).restore(source, model_type)

    def deserialize_storage(self, source: dict) -> storage_data_dto:
        """Совместимый вход для снимка хранилища; поля берутся из DTO рефлексией."""
        return self.deserialize(source, storage_data_dto)

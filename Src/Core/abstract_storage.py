from abc import ABC, abstractmethod
from contextlib import AbstractContextManager

from Src.Core.entity_model import entity_model


class abstract_storage(ABC):
    """Контракт хранения доменных объектов для сценариев CRUD."""

    @abstractmethod
    def model_types(self) -> dict[str, type[entity_model]]:
        """Возвращает имена коллекций и классы сущностей."""

    @abstractmethod
    def entities(self, collection: str) -> list[entity_model]:
        """Возвращает сущности коллекции."""

    @abstractmethod
    def get_entity(self, collection: str, code: str) -> entity_model:
        """Возвращает сущность или вызывает KeyError."""

    @abstractmethod
    def save_entity(self, collection: str, entity: entity_model) -> None:
        """Добавляет сущность с уникальным кодом."""

    @abstractmethod
    def delete_entity(self, collection: str, code: str) -> None:
        """Удаляет сущность по коду."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager:
        """Предоставляет копию данных с фиксацией только при успехе."""

from abc import ABC, abstractmethod
from typing import Any

from Src.Core.abstract_model_deserializer import abstract_model_deserializer


class abstract_deserialize_factory(ABC):
    """Определяет контракт выбора обработчика по ожидаемому типу значения."""
    @abstractmethod
    def create(self, model_type: Any) -> abstract_model_deserializer:
        """Выбрать обработчик по ожидаемому типу, включая аннотации коллекций."""

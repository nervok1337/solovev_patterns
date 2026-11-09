from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


# Ожидаемый тип может быть классом, list[Dto], Union и т.д.
restore_model = Callable[[object, Any], object]


class abstract_model_deserializer(ABC):
    """Контракт восстановления значения, не требующий наследования модели."""

    @abstractmethod
    def matches(self, source: object) -> bool:
        """Проверить форму данных без создания модели (для выбора Union)."""

    @abstractmethod
    def restore(self, source: object, restore: restore_model) -> object:
        """Восстановить значение, передавая вложения общей функции."""

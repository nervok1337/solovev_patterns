from abc import ABC, abstractmethod

from Src.Core.abstract_covertor import abstract_covertor


class abstract_convert_factory(ABC):
    """Задаёт интерфейс выбора конвертера для исходного значения."""

    @abstractmethod
    def create(
        self, source: object, ancestors: list[object] | None = None
    ) -> abstract_covertor:
        """Возвращает обработчик значения с контекстом вложенного обхода."""
        pass

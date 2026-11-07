from abc import ABC, abstractmethod
from collections.abc import Callable

from Src.Core.entity_model import entity_model


# Обработчик вложений получает данные и ожидаемый тип модели.
restore_model = Callable[[dict, type[entity_model]], entity_model]


class abstract_model_deserializer(ABC):
    """Контракт восстановления модели из данных, независимый от JSON и файлов."""

    fields: set[str]

    @abstractmethod
    def restore(self, source: dict, restore: restore_model) -> entity_model:
        """Создать модель, поручая восстановление вложений переданной функции."""
        pass


class abstract_deserialize_factory(ABC):
    """Выбор обработчика по ожидаемому типу модели."""

    @abstractmethod
    def create(self, model_type: type[entity_model]) -> abstract_model_deserializer:
        pass

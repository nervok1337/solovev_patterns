from enum import Enum

from Src.Core.abstract_model_deserializer import restore_model
from Src.Core.exception import arguments_exception
from Src.Logics.value_deserializer import value_deserializer


class text_deserializer(value_deserializer):
    """Стандартные типы с текстовым JSON-представлением."""

    def matches(self, source: object) -> bool:
        """Проверяет строковое представление даты, времени или значения перечисления."""
        return isinstance(source, str)

    def restore(self, source: object, restore: restore_model) -> object:
        """Создаёт значение перечисления либо разбирает дату или время в формате ISO."""
        if not self.matches(source):
            raise arguments_exception("source", "Ожидается строка!")
        if issubclass(self.model_type, Enum):
            return self.model_type(source)
        return self.model_type.fromisoformat(source)

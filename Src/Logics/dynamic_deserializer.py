from Src.Core.common import common
from Src.Core.abstract_model_deserializer import restore_model
from Src.Core.exception import arguments_exception
from Src.Logics.value_deserializer import value_deserializer


class dynamic_deserializer(value_deserializer):
    """Обрабатывает JSON-значения без указанного конкретного класса модели."""
    def matches(self, source: object) -> bool:
        """Проверяет, является ли источник простым значением, списком или словарём."""
        return common.is_simple_value(source) or isinstance(source, (list, dict))

    def restore(self, source: object, restore: restore_model) -> object:
        # Без аннотации конкретной модели сохраняем обычные JSON-значения.
        """Передаёт значение обработчику его фактического типа, сохраняя структуру JSON."""
        if not self.matches(source):
            raise arguments_exception("source", "Ожидается JSON-значение!")
        return restore(source, type(source))

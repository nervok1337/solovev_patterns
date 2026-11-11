from math import isfinite

from Src.Core.abstract_model_deserializer import abstract_model_deserializer, restore_model
from Src.Core.exception import arguments_exception


class value_deserializer(abstract_model_deserializer):
    """Восстанавливает простое значение с проверкой ожидаемого типа."""
    def __init__(self, model_type):
        """Сохраняет ожидаемый тип восстанавливаемого значения."""
        self.model_type = model_type

    def matches(self, source: object) -> bool:
        """Проверяет точный тип, разрешая целое число для ожидаемого float."""
        return type(source) is self.model_type or (
            self.model_type is float and type(source) is int
        )

    def restore(self, source: object, restore: restore_model) -> object:
        """Возвращает проверенное значение, отклоняя бесконечные числа и переполнение."""
        if not self.matches(source):
            raise arguments_exception("source", f"Ожидается {self.model_type}!")
        if self.model_type is float:
            try:
                value = float(source)
            except OverflowError as error:
                raise arguments_exception("source", "Число слишком велико!") from error
            if not isfinite(value):
                raise arguments_exception("source", "Ожидается конечное число!")
            return value
        return source

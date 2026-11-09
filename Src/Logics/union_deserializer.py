from typing import get_args

from Src.Core.abstract_deserialize_factory import abstract_deserialize_factory
from Src.Core.abstract_model_deserializer import restore_model
from Src.Core.exception import arguments_exception
from Src.Logics.value_deserializer import value_deserializer


class union_deserializer(value_deserializer):
    """Выбирает подходящий вариант объединения типов по структуре входных данных."""
    def __init__(self, model_type, factory: abstract_deserialize_factory):
        """Сохраняет объединение типов и фабрику для проверки его вариантов."""
        super().__init__(model_type)
        self.factory = factory

    def matches(self, source: object) -> bool:
        """Проверяет, подходит ли источник хотя бы одному варианту объединения."""
        return any(self.factory.create(item).matches(source)
                   for item in get_args(self.model_type))

    def restore(self, source: object, restore: restore_model) -> object:
        """Предпочитает точный тип, иначе требует единственного подходящего варианта."""
        candidates = [item for item in get_args(self.model_type)
                      if self.factory.create(item).matches(source)]
        if type(source) in candidates:
            return restore(source, type(source))
        if len(candidates) != 1:
            raise arguments_exception("source", "Нельзя однозначно выбрать тип из Union!")
        return restore(source, candidates[0])

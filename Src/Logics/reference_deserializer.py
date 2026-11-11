from inspect import Parameter, signature
from typing import get_type_hints

from Src.Core.common import common
from Src.Core.abstract_model_deserializer import restore_model
from Src.Core.exception import arguments_exception
from Src.Logics.value_deserializer import value_deserializer


class reference_deserializer(value_deserializer):
    """Получает схему объекта из конструктора, свойств и аннотаций класса."""

    def __init__(self, model_type):
        """Получает свойства, типы и обязательные параметры конструктора через рефлексию."""
        super().__init__(model_type)
        self.parameters = {
            name: parameter for name, parameter in signature(model_type).parameters.items()
            if parameter.kind not in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD)
        }
        self.properties = {
            name: getattr(model_type, name) for name in common.get_fields(model_type)
        }
        self.types = {name: hint for name, hint in get_type_hints(model_type).items()
                      if not name.startswith("_")}
        for name, prop in self.properties.items():
            hint = get_type_hints(prop.fget).get("return")
            if hint is not None:
                self.types[name] = hint
        # Конструктор точнее описывает вход: например, допускает None для базы.
        self.types.update({name: hint for name, hint in get_type_hints(model_type.__init__).items()
                           if name in self.parameters})
        self.fields = set(self.parameters) | set(self.properties) | set(self.types)
        self.required = {name for name, param in self.parameters.items()
                         if param.default is Parameter.empty}

    def matches(self, source: object) -> bool:
        """Проверяет наличие обязательных параметров и отсутствие неизвестных полей."""
        return (isinstance(source, dict) and self.required <= source.keys()
                and source.keys() <= self.fields)

    def restore(self, source: object, restore: restore_model) -> object:
        """Восстанавливает вложения, вызывает конструктор и сеттеры, сверяет вычисляемые свойства."""
        if not self.matches(source):
            raise arguments_exception("source", f"Неверные поля {self.model_type.__name__}!")
        values = {}
        for name, value in source.items():
            if name not in self.types:
                raise arguments_exception(name, "Для восстановления нужна аннотация типа!")
            values[name] = restore(value, self.types[name])
        positional = [values[name] if name in values else param.default
                      for name, param in self.parameters.items()
                      if param.kind is Parameter.POSITIONAL_ONLY]
        keywords = {name: values[name] for name, param in self.parameters.items()
                    if name in values and param.kind is not Parameter.POSITIONAL_ONLY}
        try:
            model = self.model_type(*positional, **keywords)
        except Exception as error:
            # Дополняем ошибку конструктора контекстом, сохраняя исходную причину.
            raise arguments_exception(
                "source",
                f"Не удалось создать {self.model_type.__name__}: {error}",
            ) from error
        for name, value in values.items():
            if name in self.parameters:
                continue
            prop = self.properties.get(name)
            if prop is None or prop.fset is not None:
                setattr(model, name, value)
        # Вычисляемые свойства проверяем после заполнения всех изменяемых полей.
        for name, prop in self.properties.items():
            if name in values and name not in self.parameters and prop.fset is None:
                if getattr(model, name) != values[name]:
                    raise arguments_exception(name, "Вычисляемое свойство не совпадает с данными!")
        return model

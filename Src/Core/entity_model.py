import uuid
from abc import ABC

from Src.Core.exception import arguments_exception


class entity_model(ABC):
    """Общая базовая модель с уникальным кодом и наименованием."""

    __name: str = ""
    __unique_code: str

    def __init__(self) -> None:
        """Создаёт модель с уникальным идентификатором."""
        super().__init__()
        self.__unique_code = uuid.uuid4().hex

    @property
    def id(self) -> str:
        """Возвращает идентификатор сущности."""
        return self.__unique_code

    @property
    def name(self) -> str:
        """Возвращает наименование сущности."""
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        """Устанавливает наименование сущности."""
        if value == "":
            raise ValueError("Name cannot be empty")

        self.__name = value

    @property
    def unique_code(self) -> str:
        """Возвращает уникальный код для обратной совместимости."""
        return self.__unique_code

    @unique_code.setter
    def unique_code(self, value: str) -> None:
        """Изменяет уникальный код через прежний интерфейс."""
        if value.strip() == "":
            raise arguments_exception(
                "value",
                "Некорректно передан параметр!",
            )

        self.__unique_code = value.strip()

    def __eq__(self, other: object) -> bool:
        """Сравнивает модели по уникальному коду."""
        if not isinstance(other, entity_model):
            return NotImplemented

        return self.__unique_code == other.__unique_code

  

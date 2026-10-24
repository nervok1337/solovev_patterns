from abc import ABC, abstractmethod


class abstract_covertor(ABC):
    """Задаёт общий интерфейс преобразования объекта в словарь полей."""

    @abstractmethod
    def convert(self, source: object) -> dict[str, object]:
        """Возвращает словарь: имя поля — значение поля исходного объекта."""
        pass

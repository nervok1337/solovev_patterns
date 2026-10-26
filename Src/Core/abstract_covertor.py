from abc import ABC, abstractmethod


class abstract_covertor(ABC):
    """Задаёт общий интерфейс преобразования объекта в словарь полей."""

    @abstractmethod
    def convert(
        self, source: object, field_name: str | None = None
    ) -> dict[str, object]:
        """Преобразует значение; имя поля задаёт ключ при вложенном вызове."""
        pass

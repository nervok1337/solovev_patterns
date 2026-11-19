from enum import Enum


class comparison_type_enum(str, Enum):
    """Операции сравнения строк при фильтрации доменных моделей."""

    EQUALS = "EQUALS"
    LIKE = "LIKE"


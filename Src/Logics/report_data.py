from collections.abc import Mapping, Sequence, Set

from Src.Core.common import common
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_row_dto import report_row_dto


def is_collection(value) -> bool:
    """Проверяет, является ли значение коллекцией, но не строкой."""
    return isinstance(value, (Mapping, Sequence, Set)) and not isinstance(
        value,
        (str, bytes, bytearray),
    )


def get_collection_items(source) -> list | None:
    """Возвращает элементы первого публичного свойства-коллекции."""
    for field in common.get_fields(source):
        value = getattr(source, field)
        if isinstance(value, Mapping):
            return list(value.values())
        if is_collection(value):
            return list(value)

    return None


def get_display_value(value):
    """Преобразует вложенную модель в понятное скалярное значение."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    fields = common.get_fields(value, is_common=True)
    if "name" in fields:
        return getattr(value, "name")
    if "unique_code" in fields:
        return getattr(value, "unique_code")

    return str(value)


def get_type_name(source) -> str:
    """Возвращает имя типа без технического суффикса model."""
    return source.__class__.__name__.removesuffix("_model")


def create_report_data(source) -> report_data_dto:
    """Формирует таблицу из актуальных публичных свойств объекта."""
    common.get_fields(source)
    collection_items = get_collection_items(source)
    row_sources = collection_items if collection_items else [source]

    keys = []
    fields_by_row = []
    for row_source in row_sources:
        fields = common.get_fields(row_source, is_common=True)
        fields_by_row.append(fields)
        for field in fields:
            if field not in keys:
                keys.append(field)

    rows: list[report_row_dto] = []
    for row_source, fields in zip(row_sources, fields_by_row):
        values = []
        for key in keys:
            value = ""
            if key in fields:
                value = get_display_value(getattr(row_source, key))
            values.append(value)
        rows.append(report_row_dto(values))

    numeric_columns = frozenset(
        index
        for index in range(len(keys))
        if rows
        and all(
            isinstance(row.values[index], (int, float))
            and not isinstance(row.values[index], bool)
            for row in rows
            if row.values[index] != ""
        )
    )

    name = getattr(source, "name", get_type_name(source))
    row_name = get_type_name(row_sources[0]) if collection_items else None
    return report_data_dto(
        root_name=get_type_name(source),
        row_name=row_name,
        name=str(name),
        keys=keys,
        headers=keys.copy(),
        rows=rows,
        numeric_columns=numeric_columns,
    )

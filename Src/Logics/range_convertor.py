from Src.Logics.reference_convertor import reference_convertor
from Src.Models.range_model import range_model


class range_convertor(reference_convertor):
    """Сохраняет базовую единицу измерения без самоссылки в base_range."""

    def _get_fields(self, source: object) -> dict[str, object]:
        """Представляет самоссылку базовой единицы пустым значением поля."""
        fields = super()._get_fields(source)
        if (
            isinstance(source, range_model)
            and source.base_range is source
            and source.conversion_factor == 1
        ):
            fields["base_range"] = None
        return fields

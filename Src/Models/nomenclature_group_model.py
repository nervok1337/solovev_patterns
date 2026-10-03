from Src.Core.entity_model import entity_model


class nomenclature_group_model(entity_model):
    """Группа, объединяющая элементы номенклатуры."""

    def __init__(self, name: str) -> None:
        """Создаёт группу номенклатуры с указанным наименованием."""
        super().__init__()
        self.name = name

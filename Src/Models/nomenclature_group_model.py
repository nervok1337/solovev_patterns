from Src.Core.entity_model import entity_model


class nomenclature_group_model(entity_model):
    """Группа, объединяющая элементы номенклатуры."""

    @classmethod
    def create(cls, name: str) -> "nomenclature_group_model":
        """Создаёт группу номенклатуры фабричным методом."""
        return cls(name)

    def __init__(self, name: str) -> None:
        """Создаёт группу номенклатуры с указанным наименованием."""
        super().__init__()
        self.name = name

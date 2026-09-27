from Src.Core.entity_model import entity_model


class warehouse_model(entity_model):
    """Склад, в разрезе которого ведётся учёт остатков."""

    def __init__(self, name: str) -> None:
        """Создаёт склад с указанным наименованием."""
        super().__init__()
        self.name = name

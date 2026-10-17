from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_type_dto import report_type_enum
from abc import ABC, abstractmethod


class abstarct_report_factory(ABC):
    """
    Абстрактная фабрика отчетов
    """
    @abstractmethod
    def create(self, report_type: report_type_enum) -> abstract_report:
        pass

    @abstractmethod
    def create_default(self) -> abstract_report:
        """Создаёт отчёт в формате, указанном в настройках."""
        pass

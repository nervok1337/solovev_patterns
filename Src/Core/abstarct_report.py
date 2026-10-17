from Src.Dtos.report_result_dto import report_result_dto
from abc import ABC, abstractmethod
from Src.Core.abstract_model import abstract_model

class abstract_report(ABC):
    """
    Абстрактный класс для формирования отчета
    """
    @abstractmethod
    def build(self, source: abstract_model) -> report_result_dto:
        """
        Сформировать отчет
        """
        pass
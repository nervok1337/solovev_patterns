from Src.Dtos.report_result_dto import report_result_dto
from abc import ABC, abstractmethod
from flask import Response
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

    @abstractmethod
    def create_response(self, result: report_result_dto) -> Response:
        """Создаёт HTTP-ответ в формате конкретного отчёта."""
        pass

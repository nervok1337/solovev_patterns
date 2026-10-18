from flask import Response

from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto


class abstract_text_report(abstract_report):
    """Базовый отчёт, возвращаемый как структурированный текст."""

    content_type: str = ""

    def create_response(self, result: report_result_dto) -> Response:
        """Создаёт текстовый HTTP-ответ нужного MIME-типа."""
        return Response(result.text, content_type=self.content_type)

from flask import Response

from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto


class abstract_binary_report(abstract_report):
    """Базовый отчёт, возвращаемый пользователю как скачиваемый файл."""

    content_type: str = ""
    file_name: str = ""

    def create_response(self, result: report_result_dto) -> Response:
        """Создаёт ответ с бинарными данными и именем файла."""
        return Response(
            bytes(result.binary),
            content_type=self.content_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{self.file_name}"'
                ),
            },
        )

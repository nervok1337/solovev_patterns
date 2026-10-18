from html import escape

from Src.Core.abstract_text_report import abstract_text_report
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.report_data import create_report_data


class html_report(abstract_text_report):
    """Формирует данные сущности в виде HTML-таблицы."""

    content_type = "text/html; charset=utf-8"

    def build(self, source) -> report_result_dto:
        """Создаёт HTML-таблицу с данными сущности."""
        data = create_report_data(source)
        rows = []

        for row in data.rows:
            cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
            rows.append(f"<tr>{cells}</tr>")

        headers = "".join(
            f"<th>{escape(header)}</th>" for header in data.headers
        )
        result = report_result_dto()
        result.text = (
            f"<table><thead><tr>{headers}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
        )
        return result

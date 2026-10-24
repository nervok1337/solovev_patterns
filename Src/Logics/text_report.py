from Src.Core.abstract_text_report import abstract_text_report
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.report_data import create_report_data


class text_report(abstract_text_report):
    """Формирует данные сущности в текстовом формате."""

    content_type = "text/plain; charset=utf-8"

    def build(self, source) -> report_result_dto:
        """Создаёт текстовую таблицу с данными сущности."""
        data = create_report_data(source)
        rows = [" | ".join(data.headers)]
        for row in data.rows:
            rows.append(" | ".join(str(value) for value in row.values))

        result = report_result_dto()
        result.text = "\n".join(rows)
        return result

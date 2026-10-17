from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.report_data import create_report_data


class text_report(abstract_report):
    """Формирует данные сущности в текстовом формате."""

    def build(self, source) -> report_result_dto:
        """Создаёт текстовую таблицу с данными сущности."""
        data = create_report_data(source)
        rows = [" | ".join(data.headers)]
        rows.extend(" | ".join(str(value) for value in row) for row in data.rows)

        result = report_result_dto()
        result.text = "\n".join(rows)
        return result

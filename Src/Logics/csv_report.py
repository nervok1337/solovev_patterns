import csv
from io import StringIO

from Src.Core.abstract_binary_report import abstract_binary_report
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.report_data import create_report_data


class csv_report(abstract_binary_report):
    """Формирует данные сущности в формате CSV."""

    content_type = "text/csv; charset=utf-8"
    file_name = "report.csv"

    def build(self, source) -> report_result_dto:
        """Создаёт CSV-таблицу с данными сущности."""
        data = create_report_data(source)
        stream = StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(data.headers)
        for row in data.rows:
            writer.writerow(row.values)

        result = report_result_dto()
        content = stream.getvalue().rstrip("\n")
        result.binary = list(content.encode("utf-8"))
        return result

from xml.etree import ElementTree

from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.report_data import create_report_data


class xml_report(abstract_report):
    """Формирует данные сущности в формате XML."""

    def build(self, source) -> report_result_dto:
        """Создаёт XML-документ с данными сущности."""
        data = create_report_data(source)
        root = ElementTree.Element(data.root_name, {"name": data.name})

        for row in data.rows:
            parent = (
                ElementTree.SubElement(root, data.row_name)
                if data.row_name is not None
                else root
            )
            for key, value in zip(data.keys, row):
                ElementTree.SubElement(parent, key).text = str(value)

        result = report_result_dto()
        result.text = ElementTree.tostring(root, encoding="unicode")
        return result

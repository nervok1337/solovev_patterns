from xml.etree import ElementTree

from Src.Core.abstarct_report import abstract_report
from Src.Core.validator import validator
from Src.Dtos.report_result_dto import report_result_dto
from Src.Models.recipe_model import recipe_model


class xml_report(abstract_report):
    """Формирует состав рецепта в формате XML."""

    def build(self, source: recipe_model) -> report_result_dto:
        """Создаёт XML-документ с ингредиентами рецепта."""
        validator.validate(source, recipe_model)
        root = ElementTree.Element("recipe", {"name": source.name})

        for item in source.ingredients:
            ingredient = ElementTree.SubElement(root, "ingredient")
            ElementTree.SubElement(ingredient, "code").text = item.unique_code
            ElementTree.SubElement(ingredient, "name").text = item.name
            ElementTree.SubElement(ingredient, "gross_weight").text = str(
                item.gross_weight
            )
            ElementTree.SubElement(ingredient, "net_weight").text = str(
                item.net_weight
            )

        result = report_result_dto()
        result.text = ElementTree.tostring(root, encoding="unicode")
        return result

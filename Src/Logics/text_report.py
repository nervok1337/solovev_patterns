from Src.Core.abstarct_report import abstract_report
from Src.Models.recipe_model import recipe_model
from Src.Core.validator import validator
from Src.Dtos.report_result_dto import report_result_dto

class text_report(abstract_report):
    __recipe: recipe_model

    def build(self, source):
        validator.validate(source, recipe_model)
        self.__recipe = source

        header = "Код | Наименование | Брутто | Нетто"
        
        data=[header]
        for item in self.__recipe.ingredients:
            data.append(f"{item.unique_code} | {item.name} | {item.gross_weight} | {item.net_weight}")
        
        result=report_result_dto()
        result.text = "\n".join(data)

        return result

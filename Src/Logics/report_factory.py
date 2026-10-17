from Src.Core.abstract_report_factory import abstarct_report_factory
from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.text_report import text_report
from Src.Core.validator import argument_exception


class report_factory(abstarct_report_factory):
    """
    Реализация фабрики для построения отчетов
    """

    # Маппинг типа отчета и его реализация
    __mapping: dict[report_type_enum, type[abstract_report]]

    def __init__(self):
        self.__mapping = {}
        self.__mapping[report_type_enum.TXT] = text_report 

    def create(self ,report_type: report_type_enum) -> abstract_report:
        if report_type not in self.__mapping:
            raise argument_exception(f"Указанный тип отчета {report_type} не реализован")

        return self.__mapping[report_type]()
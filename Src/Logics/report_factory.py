from Src.Core.abstract_report_factory import abstarct_report_factory
from Src.Core.abstarct_report import abstract_report
from Src.Dtos.report_type_dto import report_type_enum
from Src.Logics.text_report import text_report
from Src.Core.validator import argument_exception, validator
from Src.Models.settings_model import settings_model


class report_factory(abstarct_report_factory):
    """
    Реализация фабрики для построения отчетов
    """

    # Маппинг типа отчета и его реализация
    __mapping: dict[report_type_enum, type[abstract_report]]
    # Настройки формата отчёта по умолчанию
    __settings: settings_model

    def __init__(self, settings: settings_model):
        """Инициализирует фабрику с настройками приложения."""
        validator.validate(settings, settings_model)
        self.__settings = settings
        self.__mapping = {}
        self.__mapping[report_type_enum.TXT] = text_report

    def create(self, report_type: report_type_enum) -> abstract_report:
        """Создаёт отчёт явно указанного формата."""
        if report_type not in self.__mapping:
            raise argument_exception(f"Указанный тип отчета {report_type} не реализован")

        return self.__mapping[report_type]()

    def create_default(self) -> abstract_report:
        """Создаёт отчёт в формате из настроек приложения."""
        return self.create(self.__settings.response_format)

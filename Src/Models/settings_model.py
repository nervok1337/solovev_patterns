from Src.Core.abstract_model import abstract_model
from Src.Models.organization_model import organization_model
from Src.Core.validator import validator

class settings_model(abstract_model):
    # Карточка организации
    __organization: organization_model = None
    # Наименование директора
    __boss_name:str = ""
    # Наименование главного бухгалтера
    __account_name:str = ""
    __is_first_start: bool = True

    @property
    def organization(self) -> organization_model:
        return self.__organization
    @organization.setter
    def organization(self, value:organization_model) -> None:
        validator.validate(value, organization_model)
        self.__organization = value

    @property
    def boss_name(self) -> str:
        return self.__boss_name
    @boss_name.setter
    def boss_name(self, value:str) -> None:
        validator.validate(value, str, 255)
        self.__boss_name = value.strip()
    
    @property
    def account_name(self) -> str:
        return self.__account_name
    @account_name.setter
    def account_name(self, value:str) -> None:
        validator.validate(value, str, 255)
        self.__account_name = value.strip()

    @property
    def is_first_start(self) -> bool:
        return self.__is_first_start

    @is_first_start.setter
    def is_first_start(self, value: bool) -> None:
        validator.validate(value, bool)
        self.__is_first_start = value



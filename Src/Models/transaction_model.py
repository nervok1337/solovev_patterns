from Src.Core.abstract_model import abstract_model
from Src.Model.range_model import range_model
from Src.Models.settings_model import storage_model
import datetime
from Src.Core.validator import argument_exception

class transaction_model(abstract_model):
    """
    Модель транзакции
    """
    __range:range_model = None
    __storage:storage_model = None
    __nomenclature:nomenclature_model = None

    #+ Поступление
    #- Списание
    __value:float
    __period:datetime.datetime

    @property
    def value(self) -> float:
        return self.__value
    @value.setter
    def value(self, source:float) -> None:
        if source == 0:
            raise argument_exception("Значение = 0 !")
        self.__value = source
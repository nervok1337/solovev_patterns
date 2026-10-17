from Src.Core.entity_model import entity_model
from Src.Core.validator import validator

class report_result_dto(entity_model):
    __text:str=""
    __binary:list

    @property
    def text(self) -> str:
        return self.__text
    @property
    def binary(self) -> list:
        return self.__binary

    @text.setter
    def text(self, value:str) -> None:
        validator.validate(value, str)
        self.__text = value
        self.__binary = []
    
    @binary.setter
    def binary(self, value:list) -> None:
        if len(value) > 0:
            self.__text = ""
            self.__binary = value
    

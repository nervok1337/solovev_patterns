# Исключение. Обработка аргументов
class arguments_exception(Exception):
    __stack_trace:str = ""
    __message:str = ""
    __field:str = ""

    def __init__(self, field, message, stack_trace = ""):
        self.__message=message.strip()
        self.__stack_trace = stack_trace.strip()
        self.__field = field.strip()
    
    def __str__(self):
        return f"Ошибка: Некорректный аргумент {self.__field}!\n{self.__message}\n{self.__stack_trace}"
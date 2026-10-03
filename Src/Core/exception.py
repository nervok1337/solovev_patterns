class arguments_exception(ValueError):
    """Ошибка, возникающая при передаче некорректного аргумента."""

    __stack_trace: str = ""
    __message: str = ""
    __field: str = ""

    def __init__(self, field: str, message: str, stack_trace: str = "") -> None:
        """Сохраняет имя поля и описание ошибки."""
        self.__message = message.strip()
        self.__stack_trace = stack_trace.strip()
        self.__field = field.strip()
        super().__init__(self.__message)

    def __str__(self) -> str:
        """Возвращает текст ошибки с именем аргумента."""
        return (
            f"Ошибка: Некорректный аргумент {self.__field}!\n"
            f"{self.__message}\n"
            f"{self.__stack_trace}"
        )

from abc import ABC


class abstract_manager(ABC):
    """
    Абстратктный класс для реализации загрузки и обработки данных
    """

    # Полный путь к файлу
    __file_name: str = ""
    # Флаг. Загрузка и обработка данных завершена успешно
    __is_loaded: bool = False
    # Сырые данные
    __data: list = []

    def load(self, file_name: str = "") -> None:
        """
        Загрузка данных
        """
        pass

    def convert(self) -> bool:
        """
        Обработать загруженные данные
        """
        return False

    @property
    def is_loaded(self) -> bool:
        """
        Флаг подготовки данных
        """
        return self.__is_loaded

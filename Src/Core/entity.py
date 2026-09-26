import uuid
from abc import ABC, abstractmethod

class entity(ABC):
    """Represents a base entity."""
    __name: str
    __unique_code: str

    def __init__(self) -> None:
        super().__init__()
        self.__unique_code = uuid.uuid().hex

    @property
    @abstractmethod
    def id(self) -> uuid.UUID:
        """Returns the entity identifier."""
        return self.__unique_code

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the entity name."""
        pass

    @name.setter
    def name(self, value: str):
        """Sets the entity name"""
        if value == "":
            raise ValueError("Name cannot be empty")
            
        self.__name = value
        

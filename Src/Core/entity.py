import uuid
from abc import ABC, abstractmethod

class entity(ABC):
    """Represents a base entity."""
    __name: str
    __id: uuid.UUID

    @property
    @abstractmethod
    def id(self) -> uuid.UUID:
        """Returns the entity identifier."""
        pass

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
        

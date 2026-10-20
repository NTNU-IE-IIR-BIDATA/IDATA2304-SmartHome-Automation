from abc import ABC, abstractmethod

from src.NetworkComponentInterface import NetworkComponentInterface

class SensorInterface(ABC):
    """Interface for sensors"""

    @abstractmethod
    def get_data(self) -> dict:
        """Get the data from the sensor"""

    @abstractmethod
    def tick(self) -> None:
        """Tick the sensor"""
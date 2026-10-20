from abc import ABC, abstractmethod

from src.NetworkComponentInterface import NetworkComponentInterface

class SensorInterface(ABC):
    """Interface for sensors"""

    @property
    @abstractmethod
    def sensor_id(self) -> str:
        """Return the sensor identifier."""

    @property
    @abstractmethod
    def sensor_type(self) -> str:
        """Return the sensor type."""

    @abstractmethod
    def get_data(self) -> dict:
        """Get the data from the sensor"""

    @abstractmethod
    def tick(self) -> None:
        """Tick the sensor"""
from abc import ABC, abstractmethod

class NetworkComponentInterface(ABC):
    """Interface for network components. Provides functionality for connecting, disconnecting"""

    @abstractmethod
    def connect(self, ip_address, port) -> None:
        """Connect to an ip address with a given port"""

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the connection. Returns True if successfully disconnected. False otherwise"""
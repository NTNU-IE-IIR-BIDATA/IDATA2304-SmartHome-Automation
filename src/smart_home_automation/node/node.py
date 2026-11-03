import asyncio
import logging
from collections.abc import Sequence
from typing import Self

from smart_home_automation.common.constants import DEFAULT_PORT, MessageType
from smart_home_automation.common.framing import encode_message

from .actuators import Actuator
from .sensors import Sensor


class SensorActuatorNode:
    """Async SAN client responsible for registering its device manifest."""

    def __init__(
        self,
        node_id: str,
        sensors: Sequence[Sensor] = (),
        actuators: Sequence[Actuator] = (),
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
    ) -> None:
        if not node_id:
            raise ValueError("node_id must not be empty")
        self.node_id = node_id
        self.sensors = tuple(sensors)
        self.actuators = tuple(actuators)
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._running: bool = False

    @property
    def is_connected(self) -> bool:
        """Return True if connection to server is currently open."""
        return self.writer is not None and not self.writer.is_closing()

    def registration_message(self) -> dict:
        return {
            "type": MessageType.REGISTER_NODE,
            "node_id": self.node_id,
            "sensors": [sensor.manifest() for sensor in self.sensors],
            "actuators": [actuator.manifest() for actuator in self.actuators],
        }

    async def connect(self) -> None:
        """Establish TCP connection to the server if not already connected."""
        if self.is_connected:
            return
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logging.info(f"Node '{self.node_id}' connected to {self.host}:{self.port}")

    async def register(self) -> None:
        """Connect to server (if not connected) and send registration manifest."""
        if not self.is_connected:
            await self.connect()
        if self.writer is None:
            raise RuntimeError(f"Node '{self.node_id}' is not connected")

        self.writer.write(encode_message(self.registration_message()))
        await self.writer.drain()
        logging.info(
            f"Node '{self.node_id}' registered manifest with {len(self.sensors)} sensor(s) "
            f"and {len(self.actuators)} actuator(s)"
        )

    async def disconnect(self) -> None:
        """Close TCP connection cleanly."""
        if self.writer is not None:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
            finally:
                self.writer = None
                self.reader = None
                logging.info(f"Node '{self.node_id}' disconnected")

    async def run(self) -> None:
        """Main SAN event loop: register and stay connected listening for messages."""
        self._running = True
        await self.register()
        try:
            while self._running and self.is_connected and self.reader is not None:
                line = await self.reader.readline()
                if not line:
                    logging.info(f"Server closed connection to node '{self.node_id}' (EOF)")
                    break
        except asyncio.CancelledError:
            pass
        finally:
            await self.disconnect()

    def stop(self) -> None:
        """Signal SAN loop to stop."""
        self._running = False
        if self.writer is not None:
            self.writer.close()

    async def __aenter__(self) -> Self:
        await self.register()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()


async def run_node(node: SensorActuatorNode) -> None:
    await node.run()

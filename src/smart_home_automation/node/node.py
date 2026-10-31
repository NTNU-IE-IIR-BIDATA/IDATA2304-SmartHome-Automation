import asyncio
from collections.abc import Sequence

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

    def registration_message(self) -> dict:
        return {
            "type": MessageType.REGISTER_NODE,
            "node_id": self.node_id,
            "sensors": [sensor.manifest() for sensor in self.sensors],
            "actuators": [actuator.manifest() for actuator in self.actuators],
        }

    async def register(self) -> None:
        reader, writer = await asyncio.open_connection(self.host, self.port)
        try:
            writer.write(encode_message(self.registration_message()))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


async def run_node(node: SensorActuatorNode) -> None:
    await node.register()
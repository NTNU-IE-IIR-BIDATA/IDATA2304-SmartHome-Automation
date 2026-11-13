import asyncio
import logging

from smart_home_automation.common.constants import SensorType

from .actuators import create_actuator
from .node import SensorActuatorNode, run_node
from .sensors import create_sensor


def create_default_node() -> SensorActuatorNode:
    """Create a default Sensor-Actuator Node for development and demonstration."""
    return SensorActuatorNode(
        node_id="living_room_01",
        sensors=[
            create_sensor(SensorType.TEMPERATURE.value, "temp_1"),
            create_sensor(SensorType.HUMIDITY.value, "hum_1"),
        ],
        actuators=[
            create_actuator("fan", "fan_1"),
        ],
    )


async def start_node(node: SensorActuatorNode | None = None) -> None:
    """Run the node client lifecycle."""
    if node is None:
        node = create_default_node()
    logging.info(
        f"Starting node '{node.node_id}' with {len(node.sensors)} sensor(s) "
        f"and {len(node.actuators)} actuator(s)"
    )
    try:
        await run_node(node)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info(f"Node '{node.node_id}' shutting down...")
    finally:
        await node.disconnect()


def main() -> None:
    """Entry point for 'uv run node'."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    try:
        asyncio.run(start_node())
    except KeyboardInterrupt:
        logging.info("Node shutdown complete.")


if __name__ == "__main__":
    main()

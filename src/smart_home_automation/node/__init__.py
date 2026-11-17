import argparse
import asyncio
import logging
from collections.abc import Sequence

from smart_home_automation.common.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    ActuatorType,
    SensorType,
)
from smart_home_automation.common.discovery import discover_server

from .actuators import create_actuator
from .node import SensorActuatorNode, run_node
from .sensors import create_sensor


def create_node(
    node_id: str,
    sensors: Sequence[tuple[str, str]] = (),
    actuators: Sequence[tuple[str, str]] = (),
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ca_file: str | None = None,
) -> SensorActuatorNode:
    """Create a node with as many sensor and actuator you want"""
    return SensorActuatorNode(
        node_id=node_id,
        sensors=[create_sensor(sensor_type, sensor_id) for sensor_type, sensor_id in sensors],
        actuators=[
            create_actuator(actuator_type, actuator_id) for actuator_type, actuator_id in actuators
        ],
        host=host,
        port=port,
        ca_file=ca_file,
    )


async def start_node(node: SensorActuatorNode) -> None:
    """Run the node client lifecycle."""
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


def _parse_component_spec(spec: str, component: str) -> tuple[str, str]:
    """Parse a CLI component specification in ``TYPE:ID`` format."""
    component_type, separator, component_id = spec.partition(":")
    if not separator or not component_type or not component_id or ":" in component_id:
        raise ValueError(f"{component} must use TYPE:ID format: {spec}")
    return component_type, component_id


def _parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a Smart Home sensor-actuator node.")
    parser.add_argument("--id", help="Unique node ID for a custom node.")
    parser.add_argument(
        "--host",
        "--ip",
        dest="host",
        default=DEFAULT_HOST,
        help=f"Server IP address or hostname (default: {DEFAULT_HOST}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server TCP port (default: {DEFAULT_PORT}).",
    )
    parser.add_argument("--ca-file", help="CA certificate file used to verify the TLS server.")

    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover the server automatically instead of providing a host and port",
    )

    sensor_types = ", ".join(sensor.value for sensor in SensorType)
    actuator_types = ", ".join(actuator.value for actuator in ActuatorType)

    parser.add_argument(
        "--sensor",
        action="append",
        default=[],
        metavar="TYPE:ID",
        help=(
            "Add a sensor, for example temperature:temp_1. Available types: "
            + sensor_types
            + ". Repeatable."
        ),
    )
    parser.add_argument(
        "--actuator",
        action="append",
        default=[],
        metavar="TYPE:ID",
        help=(
            "Add an actuator, for example fan:fan_1. Available types: "
            + actuator_types
            + ". Repeatable."
        ),
    )
    parsed = parser.parse_args(arguments)

    if parsed.id is None:
        parser.error("--id is required")
    if not parsed.sensor and not parsed.actuator:
        parser.error("at least one --sensor or --actuator is required")

    try:
        parsed.sensors = [_parse_component_spec(spec, "Sensor") for spec in parsed.sensor]
        parsed.actuators = [_parse_component_spec(spec, "Actuator") for spec in parsed.actuator]
    except ValueError as error:
        parser.error(str(error))

    return parsed


def main(arguments: Sequence[str] | None = None) -> None:
    """Entry point for ``uv run node``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parsed = _parse_arguments(arguments)
    host, port = parsed.host, parsed.port

    if parsed.discover:
        try:
            host, port = asyncio.run(discover_server())
            logging.info(f"Discovered server at {host} {port}")
        except TimeoutError:
            logging.info("Discovery timed out")
            return
    try:
        node = create_node(
            parsed.id,
            parsed.sensors,
            parsed.actuators,
            host=host,
            port=port,
            ca_file=parsed.ca_file,
        )
        asyncio.run(start_node(node))
    except KeyboardInterrupt:
        logging.info("Node shutdown complete.")


if __name__ == "__main__":
    main()

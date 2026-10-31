import asyncio

import pytest

from smart_home_automation.common.constants import ActuatorState, MessageType
from smart_home_automation.common.framing import decode_message
from smart_home_automation.node.actuators import (
    FanActuator,
    HeaterActuator,
    LockActuator,
    create_actuator,
)
from smart_home_automation.node.node import SensorActuatorNode
from smart_home_automation.node.sensors import (
    DoorSensor,
    HumiditySensor,
    TemperatureSensor,
    create_sensor,
)


def test_device_factories_create_protocol_manifests():
    assert TemperatureSensor("temp_1").manifest() == {
        "id": "temp_1",
        "type": "temperature",
        "unit": "celsius",
    }
    assert HumiditySensor("hum_1").manifest()["unit"] == "percent"
    assert DoorSensor("door_1").manifest()["unit"] == "state"
    assert FanActuator("fan_1").manifest()["state"] == "OFF"
    assert HeaterActuator("heater_1").manifest()["state"] == "OFF"
    assert LockActuator("lock_1").manifest()["state"] == "CLOSED"
    assert create_actuator("LOCK", "lock_2").state == ActuatorState.CLOSED


@pytest.mark.parametrize("factory", [create_sensor, create_actuator])
def test_unknown_device_type_is_rejected(factory):
    with pytest.raises(ValueError, match="Unsupported"):
        factory("unknown", "device_1")


def test_node_builds_register_node_message():
    node = SensorActuatorNode(
        "living_room_01",
        sensors=[create_sensor("temperature", "temp_1")],
        actuators=[create_actuator("fan", "fan_1")],
    )

    assert node.registration_message() == {
        "type": MessageType.REGISTER_NODE,
        "node_id": "living_room_01",
        "sensors": [{"id": "temp_1", "type": "temperature", "unit": "celsius"}],
        "actuators": [{"id": "fan_1", "type": "fan", "state": "OFF"}],
    }


def test_node_sends_register_node_over_tcp():
    asyncio.run(_test_node_sends_register_node_over_tcp())


async def _test_node_sends_register_node_over_tcp():
    received = []

    async def receive_registration(reader, writer):
        received.append(decode_message(await reader.readline()))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(receive_registration, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    node = SensorActuatorNode(
        "living_room_01",
        sensors=[TemperatureSensor("temp_1")],
        actuators=[FanActuator("fan_1")],
        port=port,
    )

    await node.register()
    await asyncio.sleep(0)
    server.close()
    await server.wait_closed()

    assert received == [node.registration_message()]

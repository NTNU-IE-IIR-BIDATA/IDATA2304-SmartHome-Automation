import asyncio

from smart_home_automation.common.constants import ActuatorState, ErrorCode, MessageType, SensorType
from smart_home_automation.common.framing import decode_message, encode_message
from smart_home_automation.node import _parse_arguments, create_node
from smart_home_automation.node.actuators import FanActuator
from smart_home_automation.node.node import SensorActuatorNode
from smart_home_automation.node.sensors import HumiditySensor, TemperatureSensor
from smart_home_automation.server.server import Server


def test_node_builds_register_node_message():
    node = SensorActuatorNode(
        "living_room_01",
        sensors=[TemperatureSensor("temp_1")],
        actuators=[FanActuator("fan_1")],
    )

    assert node.registration_message() == {
        "type": MessageType.REGISTER_NODE,
        "node_id": "living_room_01",
        "sensors": [{"id": "temp_1", "type": SensorType.TEMPERATURE.value, "unit": "celsius"}],
        "actuators": [{"id": "fan_1", "type": "fan", "state": ActuatorState.OFF.value}],
    }


def test_create_node_with_selected_components():
    node = create_node(
        "kitchen_01",
        sensors=[("temperature", "kitchen_temp_1")],
        actuators=[("fan", "kitchen_fan_1")],
    )

    assert node.node_id == "kitchen_01"
    assert [sensor.id for sensor in node.sensors] == ["kitchen_temp_1"]
    assert [actuator.id for actuator in node.actuators] == ["kitchen_fan_1"]


def test_parse_custom_node_arguments():
    arguments = _parse_arguments(
        [
            "--id",
            "kitchen_01",
            "--sensor",
            "temperature:kitchen_temp_1",
            "--sensor",
            "smoke:kitchen_smoke_1",
            "--actuator",
            "fan:kitchen_fan_1",
        ]
    )

    assert arguments.id == "kitchen_01"
    assert arguments.sensors == [
        ("temperature", "kitchen_temp_1"),
        ("smoke", "kitchen_smoke_1"),
    ]
    assert arguments.actuators == [("fan", "kitchen_fan_1")]


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
    await node.disconnect()
    server.close()
    await server.wait_closed()

    assert received == [node.registration_message()]


def test_node_server_end_to_end_handshake():
    asyncio.run(_test_node_server_end_to_end_handshake())


async def _test_node_server_end_to_end_handshake():
    server = Server(host="127.0.0.1", port=0)
    server_task = asyncio.create_task(server.start())

    while server.server is None or not server.server.sockets:
        await asyncio.sleep(0.01)

    port = server.server.sockets[0].getsockname()[1]
    node = SensorActuatorNode(
        "living_room_01",
        sensors=[TemperatureSensor("temp_1"), HumiditySensor("hum_1")],
        actuators=[FanActuator("fan_1")],
        port=port,
    )

    try:
        await node.register()
        assert node.is_connected is True

        # Wait briefly for server to process registration
        await asyncio.sleep(0.05)

        stored = server.state.get_node("living_room_01")
        assert stored is not None
        assert stored["connected"] is True
        assert len(stored["sensors"]) == 2
        assert len(stored["actuators"]) == 1
        assert server.state.get_connection("living_room_01") is not None

        # Clean disconnect from client
        await node.disconnect()
        assert node.is_connected is False

        # Wait briefly for server EOF handling
        await asyncio.sleep(0.05)

        updated = server.state.get_node("living_room_01")
        assert updated is not None
        assert updated["connected"] is False
        assert server.state.get_connection("living_room_01") is None
    finally:
        await node.disconnect()
        await server.stop()
        server_task.cancel()
        try:
            await server_task
        except (asyncio.CancelledError, Exception):
            pass


def test_node_executes_incoming_actuator_command():
    asyncio.run(_test_node_executes_incoming_actuator_command())


async def _test_node_executes_incoming_actuator_command():
    received = []

    async def handle_connection(reader, writer):
        await reader.readline()
        command = {
            "type": MessageType.ACTUATOR_CMD,
            "target_node_id": "living_room_01",
            "actuator_id": "fan_1",
            "command": ActuatorState.ON,
            "value": None,
        }
        writer.write(encode_message(command))
        await writer.drain()
        received.append(decode_message(await reader.readline()))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_connection, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    node = SensorActuatorNode(
        "living_room_01",
        actuators=[FanActuator("fan_1")],
        port=port,
    )

    await asyncio.wait_for(node.run(), timeout=5)
    server.close()
    await server.wait_closed()

    assert received == [
        {
            "type": MessageType.ACTUATOR_STATE,
            "node_id": "living_room_01",
            "actuator_id": "fan_1",
            "state": ActuatorState.ON.value,
            "success": True,
        }
    ]


def test_node_reports_protocol_error_and_continues_processing():
    asyncio.run(_test_node_reports_protocol_error_and_continues_processing())


async def _test_node_reports_protocol_error_and_continues_processing():
    received = []

    async def handle_connection(reader, writer):
        await reader.readline()
        writer.write(b"not valid json\n")
        await writer.drain()
        received.append(decode_message(await reader.readline()))

        command = {
            "type": MessageType.ACTUATOR_CMD,
            "target_node_id": "living_room_01",
            "actuator_id": "fan_1",
            "command": ActuatorState.ON,
            "value": None,
        }
        writer.write(encode_message(command))
        await writer.drain()
        received.append(decode_message(await reader.readline()))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_connection, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    node = SensorActuatorNode(
        "living_room_01",
        actuators=[FanActuator("fan_1")],
        port=port,
    )

    await asyncio.wait_for(node.run(), timeout=5)
    server.close()
    await server.wait_closed()

    assert received == [
        {
            "type": MessageType.ERROR,
            "code": ErrorCode.MALFORMED_JSON,
            "message": "Expecting value: line 1 column 1 (char 0)",
        },
        {
            "type": MessageType.ACTUATOR_STATE,
            "node_id": "living_room_01",
            "actuator_id": "fan_1",
            "state": ActuatorState.ON.value,
            "success": True,
        },
    ]


def test_node_rejects_unknown_actuator():
    asyncio.run(_test_node_rejects_unknown_actuator())


async def _test_node_rejects_unknown_actuator():
    received = []

    async def handle_connection(reader, writer):
        await reader.readline()
        command = {
            "type": MessageType.ACTUATOR_CMD,
            "target_node_id": "living_room_01",
            "actuator_id": "unknown",
            "command": ActuatorState.ON,
            "value": None,
        }
        writer.write(encode_message(command))
        await writer.drain()
        received.append(decode_message(await reader.readline()))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_connection, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    node = SensorActuatorNode(
        "living_room_01",
        actuators=[FanActuator("fan_1")],
        port=port,
    )

    await asyncio.wait_for(node.run(), timeout=5)
    server.close()
    await server.wait_closed()

    assert received == [
        {
            "type": MessageType.ERROR,
            "code": ErrorCode.ACTUATOR_NOT_FOUND,
            "message": "Actuator unknown does not exist on node living_room_01.",
        }
    ]


def test_node_rejects_invalid_actuator_command_without_changing_state():
    asyncio.run(_test_node_rejects_invalid_actuator_command_without_changing_state())


async def _test_node_rejects_invalid_actuator_command_without_changing_state():
    received = []

    async def handle_connection(reader, writer):
        await reader.readline()
        command = {
            "type": MessageType.ACTUATOR_CMD,
            "target_node_id": "living_room_01",
            "actuator_id": "fan_1",
            "command": ActuatorState.OPEN,
            "value": None,
        }
        writer.write(encode_message(command))
        await writer.drain()
        received.append(decode_message(await reader.readline()))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_connection, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    actuator = FanActuator("fan_1")
    node = SensorActuatorNode(
        "living_room_01",
        actuators=[actuator],
        port=port,
    )

    await asyncio.wait_for(node.run(), timeout=5)
    server.close()
    await server.wait_closed()

    assert received == [
        {
            "type": MessageType.ACTUATOR_STATE,
            "node_id": "living_room_01",
            "actuator_id": "fan_1",
            "state": ActuatorState.OFF.value,
            "success": False,
        }
    ]
    assert actuator.state is ActuatorState.OFF

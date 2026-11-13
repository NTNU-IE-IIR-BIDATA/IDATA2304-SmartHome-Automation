import asyncio

from smart_home_automation.common.constants import MessageType
from smart_home_automation.common.framing import decode_message, encode_message
from smart_home_automation.control_panel.client import ControlPanelClient


def test_control_panel_registration_message():
    client = ControlPanelClient("panel_01", "OWNER")

    assert client.registration_message() == {
        "type": MessageType.REGISTER_PANEL,
        "client_id": "panel_01",
        "role": "OWNER",
    }


def test_control_panel_sends_registration_over_tcp():
    asyncio.run(_test_control_panel_sends_registration_over_tcp())


async def _test_control_panel_sends_registration_over_tcp():
    received = []

    async def receive_registration(reader, writer):
        received.append(decode_message(await reader.readline()))
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(receive_registration, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = ControlPanelClient("panel_01", "OWNER", port=port)

    try:
        await client.register()
        await asyncio.sleep(0)
        await client.disconnect()
    finally:
        server.close()
        await server.wait_closed()

    assert received == [client.registration_message()]


def test_control_panel_merges_system_state_and_sensor_data():
    asyncio.run(_test_control_panel_merges_system_state_and_sensor_data())


async def _test_control_panel_merges_system_state_and_sensor_data():
    client = ControlPanelClient("panel_01", "OWNER")
    system_state = {
        "type": MessageType.SYSTEM_STATE,
        "nodes": [
            {
                "node_id": "living_room_01",
                "connected": True,
                "sensors": [{"id": "temp_1", "type": "temperature", "unit": "celsius"}],
                "actuators": [],
            }
        ],
    }
    sensor_data = {
        "type": MessageType.SENSOR_DATA,
        "node_id": "living_room_01",
        "sensor_id": "temp_1",
        "value": 22.5,
        "unit": "celsius",
        "timestamp": 123.0,
    }

    client._update_state(system_state)
    client._update_state(sensor_data)

    assert client.state["nodes"][0]["sensors"][0]["value"] == 22.5
    assert client.state["nodes"][0]["sensors"][0]["timestamp"] == 123.0


def test_control_panel_read_loop_stops_on_eof():
    asyncio.run(_test_control_panel_read_loop_stops_on_eof())


async def _test_control_panel_read_loop_stops_on_eof():
    async def close_connection(reader, writer):
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(close_connection, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = ControlPanelClient("panel_01", "OWNER", port=port)

    try:
        await client.connect()
        await client.read_loop()
        assert client._running is False
    finally:
        await client.disconnect()
        server.close()
        await server.wait_closed()


def test_control_panel_read_loop_updates_cache():
    asyncio.run(_test_control_panel_read_loop_updates_cache())


async def _test_control_panel_read_loop_updates_cache():
    system_state = {
        "type": MessageType.SYSTEM_STATE,
        "nodes": [
            {
                "node_id": "living_room_01",
                "connected": True,
                "sensors": [{"id": "temp_1", "type": "temperature", "unit": "celsius"}],
                "actuators": [],
            }
        ],
    }
    sensor_data = {
        "type": MessageType.SENSOR_DATA,
        "node_id": "living_room_01",
        "sensor_id": "temp_1",
        "value": 24.0,
        "unit": "celsius",
        "timestamp": 123.0,
    }

    async def send_updates(reader, writer):
        writer.write(encode_message(system_state))
        writer.write(encode_message(sensor_data))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(send_updates, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = ControlPanelClient("panel_01", "OWNER", port=port)

    try:
        await client.connect()
        await client.read_loop()
        assert client.state["nodes"][0]["sensors"][0]["value"] == 24.0
    finally:
        await client.disconnect()
        server.close()
        await server.wait_closed()

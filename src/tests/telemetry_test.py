import asyncio
from unittest.mock import AsyncMock, Mock

from smart_home_automation.common.framing import decode_message
import pytest

from smart_home_automation.node.node import SensorActuatorNode
from smart_home_automation.common.constants import MessageType

class FakeSensor:
    id = "door_1"
    unit = "state"

    def read_value(self) -> bool:
        return False



def test_sensor_data_message():
    node = SensorActuatorNode(node_id="room")
    sensor = FakeSensor()

    message = node.sensor_data_message(sensor)

    assert message ["type"] == MessageType.SENSOR_DATA
    assert message ["node_id"] == "room"
    assert message ["sensor_id"] == "door_1"
    assert message ["value"] is False
    assert message["unit"] == "state"
    assert isinstance(message["timestamp"], float)

def test_send_sensor_data():
    node = SensorActuatorNode(
        node_id="room",
        sensors=[FakeSensor()],
    )

    writer = Mock()
    writer.is_closing.return_value = False
    writer.drain = AsyncMock()
    node.writer = writer

    asyncio.run(node.send_sensor_data())

    writer.write.assert_called_once()
    writer.drain.assert_awaited_once()

    sent_bytes = writer.write.call_args.args[0]
    message = decode_message(sent_bytes)

    assert message["type"] == MessageType.SENSOR_DATA
    assert message["node_id"] == "room"
    assert message["sensor_id"] == "door_1"
    assert message["value"] is False

def test_telemetry_loop_repeats_and_stops(monkeypatch):
    node = SensorActuatorNode(node_id="room")
    node.writer = Mock()
    node.writer.is_closing.return_value = False
    node._running = True
    node.send_sensor_data = AsyncMock()

    pauses = []

    async def fake_sleep(seconds):
        pauses.append(seconds)
        if len(pauses) == 2:
            node._running = False

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    asyncio.run(node.telemetry_loop())

    assert node.send_sensor_data.await_count == 2
    assert pauses == [5, 5]

def test_run_stops_telemetry_on_disconnect():
    async def scenario():
        node = SensorActuatorNode(node_id="room")
        started = asyncio.Event()
        stopped = asyncio.Event()

        async def fake_telemetry():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        async def fake_readline():
            await started.wait()
            return b""

        node.register = AsyncMock()
        node.disconnect = AsyncMock()
        node.telemetry_loop = fake_telemetry

        node.writer = Mock()
        node.writer.is_closing.return_value = False
        node.reader = Mock()
        node.reader.readline = fake_readline

        await asyncio.wait_for(node.run(), timeout=1)

        assert started.is_set()
        assert stopped.is_set()
        assert node._running is False
        node.register.assert_awaited_once()
        node.disconnect.assert_awaited_once()

    asyncio.run(scenario())
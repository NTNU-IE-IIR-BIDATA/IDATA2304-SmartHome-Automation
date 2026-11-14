import asyncio
import json
import unittest

from smart_home_automation.common.constants import ErrorCode, SensorType
from smart_home_automation.common.messages import ProtocolError
from smart_home_automation.server.server import Server
from smart_home_automation.server.state import ServerState


class TestServerState(unittest.TestCase):
    def setUp(self):
        self.state = ServerState()
        self.connection = object()
        self.sensors = [{"id": "temp_1", "type": SensorType.TEMPERATURE.value, "unit": "celsius"}]
        self.actuators = [{"id": "fan_1", "type": "fan", "state": "OFF"}]

    def register(self, node_id="room", connection=None):
        self.state.register_node(
            node_id,
            self.sensors,
            self.actuators,
            self.connection if connection is None else connection,
        )

    def test_get_sensor(self):
        self.register()

        sensor = self.state.get_sensor("room", "temp_1")
        self.assertIsNotNone(sensor)
        self.assertEqual(sensor["id"], "temp_1")
        self.assertEqual(sensor["unit"], "celsius")

        # sensor not found
        self.assertIsNone(self.state.get_sensor("room", "temp_2"))

        # node not found
        self.assertIsNone(self.state.get_sensor("bedroom", "temp_1"))

    def test_update_sensor_data_success(self):
        self.register()

        self.state.update_sensor_data(
            node_id="room",
            sensor_id="temp_1",
            value=23,
            unit="celsius",
            timestamp=1234567543,
            connection=self.connection,
        )
        sensor = self.state.get_sensor("room", "temp_1")

        self.assertEqual(sensor["value"], 23)
        self.assertEqual(sensor["unit"], "celsius")
        self.assertEqual(sensor["timestamp"], 1234567543)

    def test_update_sensor_data_node_not_found(self):
        with self.assertRaises(ProtocolError) as ctx:
            self.state.update_sensor_data(
                node_id="no_room", sensor_id="temp_1", value=20.1, connection=self.connection
            )
        self.assertEqual(ctx.exception.code, ErrorCode.NODE_NOT_FOUND)

    def test_update_sensor_data_auth_failed(self):
        self.register()
        wrong_conn = object()

        # wrong connection
        with self.assertRaises(ProtocolError) as ctx:
            self.state.update_sensor_data(
                node_id="room", sensor_id="temp_1", value=20.1, connection=wrong_conn
            )
        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_FAILED)

        # missing connection
        with self.assertRaises(ProtocolError) as ctx:
            self.state.update_sensor_data(
                node_id="room", sensor_id="temp_1", value=20.1, connection=None
            )
        self.assertEqual(ctx.exception.code, ErrorCode.AUTH_FAILED)

    def test_update_sensor_data_sensor_not_found(self):
        self.register()

        with self.assertRaises(ProtocolError) as ctx:
            self.state.update_sensor_data(
                node_id="room", sensor_id="no_sensor", value=20.1, connection=self.connection
            )

        self.assertEqual(ctx.exception.code, ErrorCode.INVALID_SCHEMA)

    def test_empty_snapshot(self):
        self.assertEqual(self.state.system_state(), {"type": "SYSTEM_STATE", "nodes": []})

    def test_register_and_lookup(self):
        self.register()
        node = self.state.get_node("room")
        self.assertTrue(node["connected"])
        self.assertEqual(node["sensors"], self.sensors)
        self.assertEqual(node["actuators"], self.actuators)
        self.assertIs(self.state.get_connection("room"), self.connection)
        json.dumps(self.state.system_state())

    def test_multiple_nodes(self):
        self.register()
        self.register("kitchen", object())
        self.assertEqual(len(self.state.system_state()["nodes"]), 2)

    def test_duplicate_does_not_replace_owner(self):
        self.register()
        other = object()
        with self.assertRaises(ProtocolError):
            self.register(connection=other)
        self.state.disconnect(other)
        self.assertIs(self.state.get_connection("room"), self.connection)
        self.assertTrue(self.state.get_node("room")["connected"])

    def test_connection_cannot_register_two_nodes(self):
        self.register()
        with self.assertRaises(ProtocolError):
            self.register("kitchen")
        self.assertIsNone(self.state.get_node("kitchen"))

    def test_disconnect_retains_manifest(self):
        self.register()
        self.assertEqual(self.state.disconnect(self.connection), "room")
        self.assertFalse(self.state.get_node("room")["connected"])
        self.assertEqual(self.state.get_node("room")["sensors"], self.sensors)
        self.assertIsNone(self.state.get_connection("room"))

    def test_reconnect_ignores_old_disconnect(self):
        self.register()
        self.state.disconnect(self.connection)
        new = object()
        self.register(connection=new)
        self.state.disconnect(self.connection)
        self.assertIs(self.state.get_connection("room"), new)
        self.assertTrue(self.state.get_node("room")["connected"])

    def test_snapshots_do_not_expose_internal_data(self):
        self.register()
        self.sensors[0]["unit"] = "changed"
        self.state.get_node("room")["sensors"].clear()
        self.state.system_state()["nodes"][0]["actuators"].clear()
        self.assertEqual(self.state.get_node("room")["sensors"][0]["unit"], "celsius")
        self.assertEqual(len(self.state.get_node("room")["actuators"]), 1)

    def test_invalid_manifests_leace_state_unchanged(self):
        for invalid in [None, [None], [{}], self.sensors * 2]:
            with self.subTest(manifest=invalid):
                with self.assertRaises(ProtocolError):
                    self.state.register_node("room", invalid, [], self.connection)
                self.assertEqual(self.state.system_state()["nodes"], [])

    def test_unknown_node_and_disconnect(self):
        self.assertIsNone(self.state.get_node("missing"))
        self.assertIsNone(self.state.get_connection("missing"))
        self.assertIsNone(self.state.disconnect(object()))

    def test_invalid_node_ids(self):
        for node_id in [None, "", " ", "ALL"]:
            with self.subTest(node_id=node_id):
                with self.assertRaises(ProtocolError):
                    self.register(node_id)

    def test_register_and_disconnect_panel(self):
        connection = object()

        self.state.register_panel("panel_1", "OWNER", connection)

        self.assertEqual(
            self.state.get_panel_connections(),
            [connection],
        )

        result = self.state.disconnect(connection)

        self.assertEqual(result, "panel_1")
        self.assertEqual(self.state.get_panel_connections(), [])

    def test_duplicate_panel_keeps_original_connection(self):
        first = object()
        second = object()

        self.state.register_panel("panel_1", "OWNER", first)

        with self.assertRaises(ProtocolError):
            self.state.register_panel("panel_1", "OWNER", second)

        self.state.disconnect(second)

        self.assertEqual(
            self.state.get_panel_connections(),
            [first],
        )

class TestStateTCP(unittest.IsolatedAsyncioTestCase):
    async def test_registration_duplicate_and_disconnect(self):
        server = Server()
        listener = await asyncio.start_server(server.handle_client, "127.0.0.1", 0)
        port = listener.sockets[0].getsockname()[1]
        writers = []

        async def wait_for(predicate):
            for _ in range(100):
                if predicate():
                    return
                await asyncio.sleep(0.01)
            self.fail("Server did not update its state within one second")

        try:
            _, first = await asyncio.open_connection("127.0.0.1", port)
            writers.append(first)
            registration = (
                json.dumps(
                    {
                        "type": "REGISTER_NODE",
                        "node_id": "room",
                        "sensors": [
                            {
                                "id": "temp_1",
                                "type": SensorType.TEMPERATURE.value,
                            }
                        ],
                        "actuators": [],
                    }
                ).encode()
                + b"\n"
            )
            first.write(registration)
            await first.drain()
            await wait_for(lambda: server.state.get_connection("room") is not None)
            reader, second = await asyncio.open_connection("127.0.0.1", port)
            writers.append(second)
            second.write(registration)
            await second.drain()
            reply = json.loads(await asyncio.wait_for(reader.readline(), 1))
            self.assertEqual(reply["code"], "ERR_INVALID_SCHEMA")
            second.close()
            await second.wait_closed()
            self.assertTrue(server.state.get_node("room")["connected"])
            first.close()
            await first.wait_closed()
            await wait_for(lambda: not server.state.get_node("room")["connected"])
        finally:
            for writer in writers:
                writer.close()
                await writer.wait_closed()
            listener.close()
            await listener.wait_closed()


if __name__ == "__main__":
    unittest.main()

import asyncio
import unittest
from unittest.mock import patch

from textual.widgets import DataTable

from smart_home_automation.control_panel.client import ControlPanelClient
from smart_home_automation.control_panel.ui import ControlPanelApp
from smart_home_automation.node.node import SensorActuatorNode
from smart_home_automation.node.sensors import TemperatureSensor
from smart_home_automation.server.server import Server


async def wait_until(condition):
    async with asyncio.timeout(5):
        while not condition():
            await asyncio.sleep(0.01)


class TestEndToEnd(unittest.IsolatedAsyncioTestCase):
    async def test_sensor_data_reaches_ui_over_tcp(self):
        server = Server()
        handlers = set()

        async def handle_connection(reader, writer):
            task = asyncio.current_task()
            handlers.add(task)
            try:
                await server.handle_client(reader, writer)
            finally:
                handlers.discard(task)

        listener = await asyncio.start_server(handle_connection, "127.0.0.1", 0)
        port = listener.sockets[0].getsockname()[1]

        sensor = TemperatureSensor("temp_1")
        node = SensorActuatorNode(
            "test_room",
            sensors=[sensor],
            port=port,
        )
        client = ControlPanelClient(
            "test_panel",
            "OWNER",
            port=port,
        )
        app = ControlPanelApp(client=client)

        try:
            await node.register()

            # Send a measurement before the panel connects.
            with patch.object(sensor, "read_value", return_value=21.0):
                await node.send_sensor_data()

            def initial_measurement_received():
                nodes = server.state.system_state()["nodes"]
                return len(nodes) == 1 and nodes[0]["sensors"][0].get("value") == 21.0

            await wait_until(initial_measurement_received)

            async with app.run_test():
                table = app.query_one("#sensor_table", DataTable)
                await wait_until(lambda: table.row_count == 1)

                # The initial snapshot must contain the first measurement.
                self.assertEqual(
                    table.get_row_at(0)[:5],
                    ["test_room", "temp_1", "temperature", "21.0", "celsius"],
                )

                # Later measurements must update the same row over TCP.
                for value in (22.5, 23.0):
                    with patch.object(sensor, "read_value", return_value=value):
                        await node.send_sensor_data()

                    await wait_until(lambda: table.get_row_at(0)[3] == str(value))
                    self.assertEqual(table.row_count, 1)
                    self.assertEqual(
                        client.state["nodes"][0]["sensors"][0]["value"],
                        value,
                    )

                # End the client loop before closing the test UI.
                client.stop()
                async with asyncio.timeout(5):
                    await app.workers.wait_for_complete()

                self.assertFalse(client.is_connected)

        finally:
            await client.disconnect()
            await node.disconnect()
            listener.close()
            await listener.wait_closed()

            if handlers:
                await asyncio.wait_for(
                    asyncio.gather(*list(handlers)),
                    timeout=5,
                )

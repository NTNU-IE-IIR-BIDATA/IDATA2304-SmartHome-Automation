import unittest

from textual.widgets import DataTable

from smart_home_automation.common.constants import MessageType
from smart_home_automation.control_panel.client import ControlPanelClient
from smart_home_automation.control_panel.ui import ControlPanelApp


class TestControlPanelUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.snapshot = {
            "type": MessageType.SYSTEM_STATE,
            "nodes": [
                {
                    "node_id": "living_room_01",
                    "connected": True,
                    "sensors": [
                        {
                            "id": "temp_1",
                            "type": "temperature",
                            "unit": "celsius",
                            "value": 21.0,
                        },
                        {
                            "id": "hum_1",
                            "type": "humidity",
                            "unit": "percent",
                        },
                    ],
                    "actuators": [],
                }
            ],
        }

    async def test_system_state_displays_sensors(self):
        app = ControlPanelApp()

        async with app.run_test():
            app.handle_server_update(self.snapshot)
            table = app.query_one("#sensor_table", DataTable)

            self.assertEqual(table.row_count, 2)
            self.assertEqual(
                table.get_row_at(0)[:5],
                ["living_room_01", "temp_1", "temperature", "21.0", "celsius"],
            )
            self.assertEqual(
                table.get_row_at(1)[:6],
                [
                    "living_room_01",
                    "hum_1",
                    "humidity",
                    "—",
                    "percent",
                    "Venter på data",
                ],
            )

    async def test_sensor_updates_reuse_existing_row(self):
        app = ControlPanelApp()
        client = ControlPanelClient("test_panel", "OWNER")
        client.state_cache = self.snapshot

        async with app.run_test():
            # Attach after mounting so no network connection is started.
            app.client = client
            app.handle_server_update(self.snapshot)
            table = app.query_one("#sensor_table", DataTable)
            temperature_before = table.get_row_at(0).copy()

            for value in (42.0, 43.5):
                app.handle_server_update(
                    {
                        "type": MessageType.SENSOR_DATA,
                        "node_id": "living_room_01",
                        "sensor_id": "hum_1",
                        "value": value,
                        "unit": "percent",
                        "timestamp": 123.0,
                    }
                )

                self.assertEqual(table.row_count, 2)
                self.assertEqual(table.get_row_at(1)[3], str(value))
                self.assertEqual(
                    table.get_row_at(1)[5],
                    "[green]OK[/green]",
                )
                self.assertEqual(
                    table.get_row_at(0),
                    temperature_before,
                )

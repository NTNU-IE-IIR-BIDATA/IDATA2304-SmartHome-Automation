import unittest
from unittest.mock import AsyncMock, MagicMock

from textual.widgets import DataTable, Input

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
                    "actuators": [
                        {"id": "fan_1", "type": "fan", "state": "OFF"},
                    ],
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
                    "Waiting for data",
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

    async def test_actuator_state_updates_existing_row(self):
        app = ControlPanelApp()

        async with app.run_test():
            app.handle_server_update(self.snapshot)
            table = app.query_one("#actuator_table", DataTable)

            self.assertEqual(table.row_count, 1)
            self.assertEqual(table.get_row_at(0)[:3], ["living_room_01", "fan_1", "fan"])
            self.assertIn("OFF", table.get_row_at(0)[3])

            app.handle_server_update(
                {
                    "type": MessageType.ACTUATOR_STATE,
                    "node_id": "living_room_01",
                    "actuator_id": "fan_1",
                    "state": "ON",
                    "success": True,
                }
            )

            self.assertEqual(table.row_count, 1)
            self.assertEqual(table.get_row_at(0)[:3], ["living_room_01", "fan_1", "fan"])
            self.assertIn("ON", table.get_row_at(0)[3])

    async def test_node_table_display_connected(self):
        app = ControlPanelApp()

        async with app.run_test():
            app.handle_server_update(self.snapshot)
            table = app.query_one("#node_table", DataTable)
            self.assertEqual(table.row_count, 1)
            self.assertEqual(table.get_row_at(0), ["living_room_01", "[green]Connected[/green]"])

            self.snapshot["nodes"][0]["connected"] = False
            app.handle_server_update(self.snapshot)
            self.assertEqual(table.row_count, 1)
            self.assertEqual(table.get_row_at(0), ["living_room_01", "[red]Not Connected[/red]"])

    async def test_command_input_sends_actuator_command(self):
        app = ControlPanelApp()
        mock_client = MagicMock(spec=ControlPanelClient)
        mock_client.is_connected = True
        mock_client.send_actuator_command = AsyncMock()

        async with app.run_test() as pilot:
            app.client = mock_client
            cmd_input = app.query_one("#cmd_input", Input)
            cmd_input.focus()
            cmd_input.value = "set living_room_01 fan_1 on"
            await pilot.press("enter")
            await pilot.pause()

            mock_client.send_actuator_command.assert_awaited_once_with(
                "living_room_01", "fan_1", "ON", None
            )
            self.assertEqual(cmd_input.value, "")

    async def test_invalid_command_input_does_not_send(self):
        app = ControlPanelApp()
        mock_client = MagicMock(spec=ControlPanelClient)
        mock_client.is_connected = True
        mock_client.send_actuator_command = AsyncMock()

        async with app.run_test() as pilot:
            app.client = mock_client
            cmd_input = app.query_one("#cmd_input", Input)
            cmd_input.focus()
            cmd_input.value = "only_two_tokens bad"
            await pilot.press("enter")
            await pilot.pause()

            mock_client.send_actuator_command.assert_not_awaited()
            self.assertEqual(cmd_input.value, "")

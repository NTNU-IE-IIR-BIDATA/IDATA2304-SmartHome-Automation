from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, RichLog, Static

from ..common.constants import AnomalySeverity, MessageType, SensorType
from ..control_panel.anomaly import AnomalyDetector
from .client import ControlPanelClient


class ControlPanelApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    DataTable {
        height: 1fr;
    }
    #tables_container {
        height: 1fr;
    }
    #sensors_panel {
        width: 3fr;
        height: 1fr;
        padding-right: 1;
    }
    #actuator_panel {
        width: 2fr;
        height: 1fr;
    }
    #alerts_panel {
        height: 10;
        border: solid red;
    }
    #cmd_input {
        dock: bottom;
        margin: 1 0;
    }
    """

    BINDINGS = [Binding("q", "quit", "Quit"), Binding("c", "clear_alerts", "Clear Alerts")]

    def __init__(
        self,
        client: ControlPanelClient | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.client = client
        self.detector = AnomalyDetector()
        self._sensor_rows = {}
        self._actuator_rows = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="tables_container"):
            with Vertical(id="sensors_panel"):
                yield Static("Sensors", classes="section_title")
                yield DataTable(id="sensor_table")
            with Vertical(id="actuator_panel"):
                yield Static("Actuators", classes="section_title")
                yield DataTable(id="actuator_table")

        with Vertical(id="alerts_panel"):
            yield Static("Anomaly Feed")
            yield RichLog(id="alert_log", highlight=True, markup=True)

        yield Input(
            placeholder="Command: <node_id> <actuator_id> <ON|OFF|OPEN|CLOSED> [value]",
            id = "cmd_input"
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#sensor_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Node", "Sensor", "Type", "Value", "Unit", "Status", "Updated")

        actuator_table = self.query_one("#actuator_table", DataTable)
        actuator_table.cursor_type = "row"
        actuator_table.add_columns("Node", "Actuator", "Type", "State", "Updated")

        if self.client is not None:
            self.client.on_update = self.handle_server_update
            self.run_worker(self._run_client(), name="panel-client")

    async def _run_client(self) -> None:
        if self.client is None:
            return

        log = self.query_one("#alert_log", RichLog)

        try:
            await self.client.run()
        except OSError as error:
            log.write(f"Connection error: {error}")
        else:
            log.write("Connection to server closed")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw_input = event.value.strip()
        event.input.value = ""

        if not raw_input:
            return

        log = self.query_one("#alert_log", RichLog)
        parts = raw_input.split()

        if self.client is None or not self.client.is_connected:
            log.write("[bold red]Not connected to server[/bold red]")
            return

        # Optional leading keyword, e.g. "set node..."
        if parts[0].lower() in ("set", "cmd"):
            parts = parts[1:]

        if len(parts) not in (3, 4):
            log.write(
                "[yellow]Usage: <node_id> <actuator_id> <command> [value][/yellow]"
            )
            return

        target_node_id, target_actuator_id, command = parts[0], parts[1], parts[2].upper()
        value: int | float | None = None

        if len(parts) == 4:
            try:
                value = int(parts[3]) if parts[3].isdigit() else float(parts[3])
            except ValueError:
                log.write(f"[yellow]Invalid value: {parts[3]}[/yellow]")
                return

        try:
            await self.client.send_actuator_command(
                target_node_id, target_actuator_id, command, value
            )
            log.write(f"[dim]Sent {target_node_id}.{target_actuator_id} -> {command}[/dim]")
        except (OSError, RuntimeError) as error:
            log.write(f"[bold red]Failed to send command: {error}[/bold red]")





    def action_clear_alerts(self) -> None:
        self.query_one("#alert_log", RichLog).clear()

    def handle_server_update(self, message: dict) -> None:

        match message["type"]:

            case MessageType.SYSTEM_STATE:
                self.load_system_state(message)

            case MessageType.ERROR:
                self.query_one("#alert_log", RichLog).write(f"Server error: {message['message']}")

            case MessageType.ACTUATOR_STATE:
                self._handle_actuator_state_update(message)


            case MessageType.SENSOR_DATA:
                self._handle_sensor_data(message)




    def load_system_state(self, state: dict) -> None:
        table = self.query_one("#sensor_table", DataTable)
        table.clear()
        self._sensor_rows.clear()

        actuator_table = self.query_one("#actuator_table", DataTable)
        actuator_table.clear()
        self._actuator_rows.clear()

        for node in state.get("nodes", []):
            node_id = node["node_id"]

            for sensor in node.get("sensors", []):
                sensor_id = sensor["id"]
                sensor_type = SensorType(sensor["type"])
                unit = sensor.get("unit", "")

                if sensor.get("value") is not None:
                    self.update_sensor(
                        node_id,
                        sensor_id,
                        sensor_type,
                        sensor["value"],
                        unit,
                    )
                else:
                    row_key = table.add_row(
                        node_id,
                        sensor_id,
                        sensor_type.value,
                        "—",
                        unit,
                        "Waiting for data",
                        "—",
                    )
                    self._sensor_rows[(node_id, sensor_id)] = row_key

            for actuator in node.get("actuators", []):
                self.update_actuator(
                    node_id,
                    actuator["id"],
                    actuator.get("state", "-"),
                    actuator.get("type", "unknown")
                )

    def update_sensor(
        self,
        node_id: str,
        sensor_id: str,
        sensor_type: SensorType,
        value: str | int | float | bool,
        unit: str,
    ) -> None:

        table = self.query_one("#sensor_table", DataTable)
        log = self.query_one("#alert_log", RichLog)

        anomaly = self.detector.evaluate(node_id, sensor_id, sensor_type, value, unit)

        if anomaly:
            if anomaly.severity == AnomalySeverity.CRITICAL:  # critical anomaly
                status_text = "[bold red]CRITICAL[/bold red]"
                log.write(f"[bold red]CRITICAL ALERT[/bold red]: {anomaly.message}")
            else:  # warning anomaly
                status_text = "[yellow]WARNING[/yellow]"
                log.write(f"[yellow]Warning[/yellow]: {anomaly.message}")
        else:
            status_text = "[green]OK[/green]"

        timestamp = datetime.now().strftime("%H:%M:%S")
        key = (node_id, sensor_id)

        row_values = (
            node_id,
            sensor_id,
            sensor_type.value,
            str(value),
            unit,
            status_text,
            timestamp,
        )

        if key in self._sensor_rows:
            row_key = self._sensor_rows[key]
            for col_key, val in zip(table.columns.keys(), row_values, strict=False):
                table.update_cell(row_key, col_key, val)
        else:
            row_key = table.add_row(*row_values)
            self._sensor_rows[key] = row_key

    def update_actuator(self,
                        node_id: str,
                        actuator_id: str,
                        state: str,
                        actuator_type: str | None = None
                        ) -> None:
        table = self.query_one("#actuator_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S")
        key = (node_id, actuator_id)

        if state in ("ON", "OPEN"):
            state_text = f"[green]{state}[/green]"
        elif state in ("OFF", "CLOSED"):
            state_text = f"[dim]{state}[/dim]"
        else:
            state_text = state

        if key in self._actuator_rows:
            row_key = self._actuator_rows[key]
            col_keys = list(table.columns.keys())
            table.update_cell(row_key, col_keys[3], state_text)
            table.update_cell(row_key, col_keys[4], timestamp)
        else:
            row_key = table.add_row(
                node_id,
                actuator_id,
                actuator_type or "unknown",
                state_text,
                timestamp
            )
            self._actuator_rows[key] = row_key

    def _handle_sensor_data(self, message: dict) -> None:
        # Guard condition
        if self.client is None:
            return

        for node in self.client.state["nodes"]:
            if node["node_id"] != message["node_id"]:
                continue

            for sensor in node.get("sensors", []):
                if sensor["id"] != message["sensor_id"]:
                    continue

                self.update_sensor(
                    node["node_id"],
                    sensor["id"],
                    SensorType(sensor["type"]),
                    message["value"],
                    message["unit"],
                )
                return

    def _handle_actuator_state_update(self, message: dict) -> None:
        node_id = message["node_id"]
        actuator_id = message["actuator_id"]
        state = message["state"]

        self.update_actuator(node_id, actuator_id, state)

        log = self.query_one("#alert_log", RichLog)

        if message["success"]:
            log.write(f"[green]Actuator {node_id}.{actuator_id} -> {state}[/green]")
        else:
            log.write(
                f"[bold red]Command failed[/bold red]: {node_id}.{actuator_id} remains {state}"
            )


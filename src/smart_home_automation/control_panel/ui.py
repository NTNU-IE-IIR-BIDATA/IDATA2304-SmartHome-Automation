from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Input, RichLog, Static

from ..common.constants import AnomalySeverity, SensorType
from ..control_panel.anomaly import AnomalyDetector


class ControlPanelApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #tables_container {
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.detector = AnomalyDetector()

        self._sensor_rows = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="tables_container"):
            yield Static("Live Sensor Telemetry", classes="section_title")
            yield DataTable(id="sensor_table")

        with Vertical(id="alerts_panel"):
            yield Static("Anomaly Feed")
            yield RichLog(id="alert_log", highlight=True, markup=True)

        yield Input(placeholder="Commands go here. Implemented in milestone 5", id="cmd_input")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#sensor_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Node", "Sensor", "Type", "Value", "Unit", "Status", "Updated")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip().lower()

        if command:
            log = self.query_one("#alert_log", RichLog)
            log.write(f"[dim](placeholder) Command received: '{command}' [/dim]")
        event.input.value = ""

    def action_clear_alerts(self) -> None:
        self.query_one("#alert_log", RichLog).clear()

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

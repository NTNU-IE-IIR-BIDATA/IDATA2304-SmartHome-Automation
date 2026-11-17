import argparse
import logging
from typing import Sequence

from common.constants import DEFAULT_HOST, DEFAULT_PORT

from .client import ControlPanelClient
from .ui import ControlPanelApp


def create_control_panel(
        panel_id: str,
        role: str,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT
        ) -> ControlPanelClient:
    """
    Create a control panel client
    :param port:
    :param host:
    :param panel_id: id of the panel
    :param role: role of the panel, e.g. owner, admin, guest
    :return: a new control panel client
    """
    return ControlPanelClient(
        client_id=panel_id,
        role=role,
        host=host,
        port=port
    )

def start_control_panel(control_panel: ControlPanelClient):
    logging.info(f"Starting control panel {control_panel.client_id}")
    app = ControlPanelApp(client=control_panel)
    try:

        app.run()
    except KeyboardInterrupt:
        logging.info(f"Shutting down panel {control_panel.client_id}")

def _parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a Smart Home Control Panel.")
    parser.add_argument(
        "--id",
        help="Unique client ID for a control panel. Default: 'panel_1'"
    )
    parser.add_argument(
        "--role",
        help="Role to assign the control panel. Default: 'OWNER'"
    )
    parser.add_argument(
        "--host",
        help=f"Host address of the server to connect to. Default: {DEFAULT_HOST}"
    )
    parser.add_argument(
        "--port",
        help=f"Server port to connect to. Default: {DEFAULT_PORT}"
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> None:
    """Entry point of 'uv run control_panel'"""
    parsed = _parse_arguments(arguments)
    control_panel = create_control_panel(
        panel_id=parsed.id,
        role=parsed.role,
        host=parsed.host,
        port=parsed.port
    )
    start_control_panel(control_panel)


if __name__ == "__main__":
    main()

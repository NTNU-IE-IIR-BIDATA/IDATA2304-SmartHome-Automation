import argparse
import asyncio
import logging
from typing import Sequence

from smart_home_automation.common.constants import DEFAULT_HOST, DEFAULT_PORT, Role
from smart_home_automation.common.discovery import discover_server

from .client import ControlPanelClient
from .ui import ControlPanelApp


def create_control_panel(
    panel_id: str,
    role: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ca_file: str | None = None,
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
        port=port,
        ca_file=ca_file,
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
        "--id", default="panel_1", help="Unique client ID for a control panel. Default: 'panel_1'"
    )
    parser.add_argument(
        "--role",
        type=str.upper,
        choices=[role.value for role in Role],
        default=Role.OWNER.value,
        help="Role to assign the control panel. Default: 'OWNER'",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host address of the server to connect to. Default: {DEFAULT_HOST}",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover the server automatically instead of providing a host and port",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port to connect to. Default: {DEFAULT_PORT}",
    )
    parser.add_argument("--ca-file", help="CA certificate file used to verify the TLS server.")
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> None:
    """Entry point of 'uv run control_panel'"""
    parsed = _parse_arguments(arguments)
    host, port = parsed.host, parsed.port

    if parsed.discover:
        try:
            host, port = asyncio.run(discover_server())
            logging.info(f"Discovered server at {host} {port}")
        except TimeoutError:
            logging.info("Discovery timed out")
            return
    control_panel = create_control_panel(
        panel_id=parsed.id,
        role=parsed.role,
        host=host,
        port=port,
        ca_file=parsed.ca_file,
    )
    start_control_panel(control_panel)


if __name__ == "__main__":
    main()

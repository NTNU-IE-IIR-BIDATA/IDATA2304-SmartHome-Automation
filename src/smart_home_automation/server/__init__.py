import argparse
import asyncio
import logging
from typing import Sequence

from smart_home_automation.common.constants import DEFAULT_HOST, DEFAULT_PORT, DISCOVERY_PORT

from .server import Server


def _parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a Smart Home Server")
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Host address for server. Default: {DEFAULT_HOST}"
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        type=int,
        help=f"Port to use for the server. Default: {DEFAULT_PORT}",
    )
    return parser.parse_args(arguments)


async def run_server(server: Server | None = None) -> None:
    if server is None:
        server = Server()

    try:
        await server.start()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info("Shutting down server...")
    finally:
        await server.stop()


def main(arguments: Sequence[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parsed = _parse_arguments(arguments)

    server = Server(host=parsed.host, port=parsed.port, discovery_port=DISCOVERY_PORT)

    try:
        asyncio.run(run_server(server))
    except KeyboardInterrupt:
        # Loop has closed cleanly
        logging.info("Server shutdown complete.")


if __name__ == "__main__":
    main()

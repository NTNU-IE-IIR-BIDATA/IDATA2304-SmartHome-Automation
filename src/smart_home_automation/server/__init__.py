import asyncio
import logging

from .server import Server


async def run_server():
    server = Server()
    try:
        await server.start()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logging.info("Shutting down server...")
    finally:
        await server.stop()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        # Loop has closed cleanly
        logging.info("Server shutdown complete.")


if __name__ == "__main__":
    main()

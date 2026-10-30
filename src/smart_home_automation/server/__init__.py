import asyncio
import logging

from .server import Server

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    server = Server()

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logging.info("Server shut down by user")

if __name__ == "__main__":
    main()
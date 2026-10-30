import asyncio
import logging
from typing import Optional

from ..common.constants import DEFAULT_PORT, MessageType
from ..common.framing import decode_message, encode_message
from ..common.messages import ProtocolError, create_error_message


class Server:

    def __init__(self, host: str ="127.0.0.1", port: int =DEFAULT_PORT, state=None):
        self.host = host
        self.port = port
        self.state = state
        self.server: Optional[asyncio.Server] = None

    async def start(self):
        """
        Start the server
        :return:
        """
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )

        addrs = ", ".join(str(sock.getsockname()) for sock in self.server.sockets)
        logging.info(f"Server listening on {addrs}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        """Stop the server gracefully"""

        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logging.info("Server stopped")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle incoming TCP client connections
        :param reader:
        :param writer:
        :return:
        """

        peer = writer.get_extra_info("peername")
        logging.info(f"New client connected: {peer}")

        try:
            await self._read_loop(reader, writer, peer)
        except ConnectionResetError:
            logging.info(f"Connection reset by {peer}")
        except Exception as e:
            logging.error(f"Unexpected error with client {peer}: {e}", exc_info=True)
        finally:
            logging.info(f"Closing connection to {peer}")
            writer.close()
            await writer.wait_closed()

    async def _read_loop(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, peer):
        """
        Read line-delimited messages from the client until EOF
        :param reader:
        :param writer:
        :param peer:
        :return:
        """

        while True:
            line = await reader.readline()

            if not line:
                logging.info(f"Client {peer} disconnected (EOF)")
                break

            try:
                message = decode_message(line)
            except ProtocolError as err:
                logging.warning(f"Protocol error from {peer}: {err.code} - {err.message}")
                await self._send_error(writer, str(err.code), err.message)
                continue

            await self._dispatch_message(message, writer, peer)

    async def _dispatch_message(self, message: dict, writer: asyncio.StreamWriter, peer):
        """
        Route a validated protocol message to its corresponding handler
        :param message:
        :param writer:
        :param peer:
        :return:
        """

        msg_type = message.get("type")

        if msg_type == MessageType.REGISTER_NODE:
            await self._handle_register_node(message, writer, peer)
        elif msg_type == MessageType.REGISTER_PANEL:
            await self._handle_register_panel(message, writer, peer)
        else:
            logging.warning(f"Unhandled message type {msg_type} from {peer}")

    async def _handle_register_node(self, message: dict, writer: asyncio.StreamWriter, peer):
        """
        Handle REGISTER_NODE messages from a Sensor-Actuator-Node
        :param message:
        :param writer:
        :param peer:
        :return:
        """

        node_id = message["node_id"]
        sensors = message.get("sensors", [])
        actuators = message.get("actuators", [])

        logging.info(
            f"Node {node_id} registered from {peer} with "
            f"{len(sensors)} sensor(s) and {len(actuators)} actuator(s)"
        )

        if self.state:
            #server state integration goes here
            pass
    async def _handle_register_panel(self, message: dict, writer: asyncio.StreamWriter, peer):
        """
        Handle REGISTER_PANEL messages from a control panel
        :param message:
        :param writer:
        :param peer:
        :return:
        """

        client_id = message["client_id"]
        role = message["role"]
        logging.info(f"Control panel {client_id} registered from {peer} with role {role}")

    async def _send_error(self, writer: asyncio.StreamWriter, code: str, message: str):
        """
        Send an ERROR response message to the client
        :param writer:
        :param code:
        :param message:
        :return:
        """
        payload = create_error_message(code, message)
        writer.write(encode_message(payload))
        await writer.drain()

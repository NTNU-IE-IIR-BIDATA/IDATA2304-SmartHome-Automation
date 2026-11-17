import asyncio
import logging

from ..common.constants import DEFAULT_PORT, MAX_MESSAGE_SIZE, ErrorCode, MessageType
from ..common.framing import decode_message, encode_message
from ..common.messages import ProtocolError, create_error_message
from .state import ServerState


class Server:
    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT, state=None):
        self.host = host
        self.port = port
        self.state = state if state is not None else ServerState()
        self.server: asyncio.Server | None = None

    async def start(self):
        """
        Start the server
        :return:
        """
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            limit=MAX_MESSAGE_SIZE,
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
            disconnected = self.state.disconnect(writer)
            if disconnected and self.state.get_node(disconnected) is not None:
                await self._broadcast_system_state()
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

        consecutive_protocol_errors = 0
        while True:
            try:
                line = await reader.readline()
            except (asyncio.LimitOverrunError, ValueError):
                await self._send_error(
                    writer,
                    ErrorCode.MALFORMED_JSON,
                    "Message exceeds 64KiB limit",
                )
                break

            if not line:
                logging.info(f"Client {peer} disconnected")
                break

            try:
                message = decode_message(line)
            except ProtocolError as err:
                consecutive_protocol_errors += 1
                logging.warning(f"Protocol error from {peer}: {err.code} - {err.message}")
                await self._send_error(writer, err.code, err.message)
                if consecutive_protocol_errors >= 3:
                    break
                continue

            consecutive_protocol_errors = 0
            try:
                await self._dispatch_message(message, writer, peer)
            except ProtocolError as err:
                await self._send_error(writer, err.code, err.message)

    async def _dispatch_message(self, message: dict, writer: asyncio.StreamWriter, peer):
        """
        Route a validated protocol message to its corresponding handler
        :param message:
        :param writer:
        :param peer:
        :return:
        """

        msg_type = message.get("type")
        match msg_type:
            case MessageType.REGISTER_NODE:
                await self._handle_register_node(message, writer, peer)

            case MessageType.REGISTER_PANEL:
                await self._handle_register_panel(message, writer, peer)

            case MessageType.SENSOR_DATA:
                await self._handle_sensor_data(message, writer, peer)

            case MessageType.ACTUATOR_CMD:
                await self._handle_actuator_command(message, writer, peer)

            case MessageType.ACTUATOR_STATE:
                await self._handle_actuator_state(message, writer, peer)

            case _:
                logging.warning(f"Unhandled message type {msg_type} from {peer}")

    async def _handle_actuator_command(self, message, writer, peer):
        if not any(
                connection is writer
                for connection in self.state.get_panel_connections()
        ):
            raise ProtocolError(
                ErrorCode.AUTH_FAILED,
                "Only registered control panels can send actuator commands",
            )

        target_node_id = message["target_node_id"]
        target_actuator_id = message["actuator_id"]
        targets = []

        for node in self.state.system_state()["nodes"]:
            node_id = node["node_id"]
            if not node["connected"]:
                continue
            if target_node_id != "ALL" and target_node_id != node_id:
                continue
            for actuator in node["actuators"]:
                if target_actuator_id == "ALL" or target_actuator_id == actuator["id"]:
                    targets.append((node_id, actuator["id"]))

        if not targets:
            if target_node_id != "ALL" and self.state.get_connection(target_node_id) is None:
                raise ProtocolError(
                    ErrorCode.NODE_NOT_FOUND,
                    f"Node {target_node_id} is not connected",
                )
            raise ProtocolError(
                ErrorCode.ACTUATOR_NOT_FOUND,
                f"Actuator {target_actuator_id} not found",
            )

        for node_id, actuator_id in targets:
            node_writer = self.state.get_connection(node_id)
            forwarded = message | {
                "target_node_id": node_id,
                "actuator_id": actuator_id,
            }
            try:
                node_writer.write(encode_message(forwarded))
                await node_writer.drain()
            except OSError as error:
                self.state.disconnect(node_writer)
                node_writer.close()
                await self._broadcast_system_state()
                raise ProtocolError(
                    ErrorCode.EXECUTION_FAILED,
                    f"Could not send command to node {node_id}",
                ) from error

            logging.info(
                "Forwarded command %s to %s.%s",
                message["command"],
                node_id,
                actuator_id,
            )

    async def _handle_actuator_state(self, message, writer, peer):
        self.state.update_actuator_state(
            node_id=message["node_id"],
            actuator_id=message["actuator_id"],
            state=message["state"],
            connection=writer,
        )

        await self._broadcast_sensor_data(message)

        logging.info(
            "Actuator state from %s.%s: %s (success=%s)",
            message["node_id"],
            message["actuator_id"],
            message["state"],
            message["success"],
        )

    async def _handle_sensor_data(self, message, writer, peer):
        """
        Handle SENSOR_DATA messages from a Sensor-Actuator-Node
        :param message:
        :param writer:
        :param peer:
        :return:
        """
        node_id = message["node_id"]
        sensor_id = message["sensor_id"]
        value = message["value"]
        unit = message.get("unit")
        timestamp = message.get("timestamp")

        self.state.update_sensor_data(
            node_id=node_id,
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            timestamp=timestamp,
            connection=writer,
        )
        await self._broadcast_sensor_data(message)
        logging.info(f"Sensor data from {node_id}.{sensor_id}: {value} {unit or ''}".strip())

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

        self.state.register_node(node_id, sensors, actuators, writer)
        await self._broadcast_system_state()

        logging.info(
            f"Node {node_id} registered from {peer} with "
            f"{len(sensors)} sensor(s) and {len(actuators)} actuator(s)"
        )

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

        self.state.register_panel(client_id, role, writer)

        snapshot = self.state.system_state()
        writer.write(encode_message(snapshot))
        await writer.drain()

        logging.info(f"Control panel {client_id} registered from {peer} with role {role}")

    async def _broadcast_sensor_data(self, message):
        payload = encode_message(message)

        for panel_writer in self.state.get_panel_connections():
            try:
                panel_writer.write(payload)
                await panel_writer.drain()
            except (ConnectionError, OSError):
                self.state.disconnect(panel_writer)
                panel_writer.close()
                logging.warning("removed deisconnected control panel")

    async def _broadcast_system_state(self):
        payload = encode_message(self.state.system_state())
        for panel_writer in self.state.get_panel_connections():
            try:
                panel_writer.write(payload)
                await panel_writer.drain()
            except (ConnectionError, OSError):
                self.state.disconnect(panel_writer)
                panel_writer.close()

    async def _send_error(self, writer: asyncio.StreamWriter, code: ErrorCode, message: str):
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

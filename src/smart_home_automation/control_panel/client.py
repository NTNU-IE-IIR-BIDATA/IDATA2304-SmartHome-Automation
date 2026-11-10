import asyncio
import logging
from copy import deepcopy
from typing import Self

from ..common.constants import DEFAULT_PORT, MessageType
from ..common.framing import decode_message, encode_message
from ..common.messages import ProtocolError


class ControlPanelClient:
    """Async TCP client for monitoring the smart-home system."""

    def __init__(
        self,
        client_id: str,
        role: str,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
    ) -> None:
        if not client_id:
            raise ValueError("client_id must not be empty")
        if not role:
            raise ValueError("role must not be empty")

        self.client_id = client_id
        self.role = role
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.state_cache: dict = {"type": MessageType.SYSTEM_STATE, "nodes": []}
        self.last_error: dict | None = None
        self._running = False

    @property
    def is_connected(self) -> bool:
        """Return True if the connection to the server is open."""
        return self.writer is not None and not self.writer.is_closing()

    @property
    def state(self) -> dict:
        """Return a copy of the current system state cache."""
        return deepcopy(self.state_cache)

    def registration_message(self) -> dict:
        return {
            "type": MessageType.REGISTER_PANEL,
            "client_id": self.client_id,
            "role": self.role,
        }

    async def connect(self) -> None:
        """Establish a TCP connection to the server if not already connected."""
        if self.is_connected:
            return

        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logging.info("Control panel '%s' connected to %s:%s", self.client_id, self.host, self.port)

    async def register(self) -> None:
        """Connect to the server and send the panel registration message."""
        if not self.is_connected:
            await self.connect()
        if self.writer is None:
            raise RuntimeError(f"Control panel '{self.client_id}' is not connected")

        self.writer.write(encode_message(self.registration_message()))
        await self.writer.drain()
        logging.info("Control panel '%s' registered with role %s", self.client_id, self.role)

    def _update_state(self, message: dict) -> None:
        if message["type"] == MessageType.SYSTEM_STATE:
            self.state_cache = deepcopy(message)
            return

        if message["type"] != MessageType.SENSOR_DATA:
            return

        for node in self.state_cache["nodes"]:
            if node.get("node_id") != message["node_id"]:
                continue
            for sensor in node.get("sensors", []):
                if sensor.get("id") != message["sensor_id"]:
                    continue
                sensor["value"] = message["value"]
                sensor["unit"] = message["unit"]
                sensor["timestamp"] = message["timestamp"]
                return

    async def read_loop(self) -> None:
        """Read and process server messages until the connection closes."""
        if self.reader is None:
            raise RuntimeError(f"Control panel '{self.client_id}' is not connected")

        self._running = True
        while self._running and self.is_connected:
            line = await self.reader.readline()
            if not line:
                logging.info("Server closed the control-panel connection")
                break

            try:
                message = decode_message(line)
            except ProtocolError as error:
                logging.warning("Protocol error from server: %s - %s", error.code, error.message)
                continue

            if message["type"] == MessageType.ERROR:
                self.last_error = message
            else:
                self._update_state(message)

        self._running = False

    async def disconnect(self) -> None:
        """Close the TCP connection cleanly."""
        self._running = False
        if self.writer is None:
            return

        try:
            self.writer.close()
            await self.writer.wait_closed()
        finally:
            self.writer = None
            self.reader = None
            logging.info("Control panel '%s' disconnected", self.client_id)

    async def run(self) -> None:
        """Register the panel and process server updates until disconnected."""
        try:
            await self.register()
            await self.read_loop()
        finally:
            await self.disconnect()

    def stop(self) -> None:
        """Signal the read loop to stop."""
        self._running = False
        if self.writer is not None:
            self.writer.close()

    async def __aenter__(self) -> Self:
        await self.register()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()
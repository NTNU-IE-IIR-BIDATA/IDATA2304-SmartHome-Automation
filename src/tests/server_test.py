import asyncio
import functools
from unittest.mock import AsyncMock, MagicMock, patch

from smart_home_automation.common.constants import ErrorCode, MessageType
from smart_home_automation.common.framing import decode_message, encode_message
from smart_home_automation.server.server import Server


def async_test(func):
    """Run an async test using standard library asyncio.run().

    This avoids needing any external pytest plugins (like pytest-asyncio or anyio).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


class TestServerUnit:
    """Fast, isolated unit tests using mocks for StreamReader and StreamWriter."""

    @async_test
    async def test_send_error(self):
        """Verify _send_error formats an ERROR message, writes to writer, and calls drain."""
        server = Server()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        await server._send_error(mock_writer, ErrorCode.MALFORMED_JSON, "Invalid JSON received")

        mock_writer.write.assert_called_once()
        written_bytes = mock_writer.write.call_args[0][0]
        decoded = decode_message(written_bytes)
        assert decoded["type"] == MessageType.ERROR
        assert decoded["code"] == ErrorCode.MALFORMED_JSON
        assert decoded["message"] == "Invalid JSON received"
        mock_writer.drain.assert_awaited_once()

    @async_test
    async def test_read_loop_handles_eof(self):
        """Verify _read_loop cleanly finishes when client disconnects (readline returns b'')."""
        server = Server()
        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(return_value=b"")  # Simulate EOF
        mock_writer = MagicMock()

        # Should exit loop immediately on EOF
        await server._read_loop(mock_reader, mock_writer, ("127.0.0.1", 12345))
        mock_reader.readline.assert_awaited_once()

    @async_test
    async def test_read_loop_catches_protocol_error(self):
        """Verify invalid message sends ERROR back to client and continues reading."""
        server = Server()
        mock_reader = MagicMock()
        # First return bad message, then EOF to exit loop
        mock_reader.readline = AsyncMock(side_effect=[b"not valid json\n", b""])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        await server._read_loop(mock_reader, mock_writer, ("127.0.0.1", 12345))

        # Check error response was sent to writer
        mock_writer.write.assert_called_once()
        sent_data = decode_message(mock_writer.write.call_args[0][0])
        assert sent_data["type"] == MessageType.ERROR
        assert sent_data["code"] == ErrorCode.MALFORMED_JSON

    @async_test
    async def test_dispatch_routes_to_register_node(self):
        """Verify _dispatch_message routes REGISTER_NODE correctly."""
        server = Server()
        mock_writer = MagicMock()
        node_msg = {
            "type": MessageType.REGISTER_NODE,
            "node_id": "test_node_01",
            "sensors": [],
            "actuators": [],
        }

        with patch.object(server, "_handle_register_node", new_callable=AsyncMock) as mock_handler:
            await server._dispatch_message(node_msg, mock_writer, ("127.0.0.1", 12345))
            mock_handler.assert_awaited_once_with(node_msg, mock_writer, ("127.0.0.1", 12345))

    @async_test
    async def test_dispatch_routes_to_register_panel(self):
        """Verify _dispatch_message routes REGISTER_PANEL correctly."""
        server = Server()
        mock_writer = MagicMock()
        panel_msg = {
            "type": MessageType.REGISTER_PANEL,
            "client_id": "panel_01",
            "role": "OWNER",
        }

        with patch.object(server, "_handle_register_panel", new_callable=AsyncMock) as mock_handler:
            await server._dispatch_message(panel_msg, mock_writer, ("127.0.0.1", 12345))
            mock_handler.assert_awaited_once_with(panel_msg, mock_writer, ("127.0.0.1", 12345))


class TestServerIntegration:
    """Integration tests: spin up server on port 0 and connect real TCP clients."""

    @async_test
    async def test_client_connect_and_malformed_json_response(self):
        # Port 0 asks the OS for any currently free ephemeral port
        server = Server(host="127.0.0.1", port=0)
        server_task = asyncio.create_task(server.start())

        while server.server is None or not server.server.sockets:
            await asyncio.sleep(0.01)

        assigned_port = server.server.sockets[0].getsockname()[1]

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", assigned_port)

            # Send malformed JSON line
            writer.write(b"this is not valid json\n")
            await writer.drain()

            # Expect ERROR response
            response_line = await reader.readline()
            response_msg = decode_message(response_line)

            assert response_msg["type"] == MessageType.ERROR
            assert response_msg["code"] == ErrorCode.MALFORMED_JSON

            # Clean client disconnect
            writer.close()
            await writer.wait_closed()
        finally:
            await server.stop()
            server_task.cancel()
            try:
                await server_task
            except (asyncio.CancelledError, Exception):
                pass

    @async_test
    async def test_client_register_node_and_disconnect(self):
        server = Server(host="127.0.0.1", port=0)
        server_task = asyncio.create_task(server.start())

        while server.server is None or not server.server.sockets:
            await asyncio.sleep(0.01)

        assigned_port = server.server.sockets[0].getsockname()[1]

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", assigned_port)

            reg_msg = {
                "type": MessageType.REGISTER_NODE,
                "node_id": "living_room_01",
                "sensors": [{"id": "temp_1", "type": "temperature", "unit": "celsius"}],
                "actuators": [{"id": "fan_1", "type": "fan", "state": "OFF"}],
            }
            writer.write(encode_message(reg_msg))
            await writer.drain()

            # Wait briefly to let server process the message
            await asyncio.sleep(0.05)

            # Close client connection cleanly
            writer.close()
            await writer.wait_closed()
        finally:
            await server.stop()
            server_task.cancel()
            try:
                await server_task
            except (asyncio.CancelledError, Exception):
                pass

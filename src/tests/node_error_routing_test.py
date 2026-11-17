import unittest
from unittest.mock import AsyncMock, MagicMock

from smart_home_automation.common.constants import ErrorCode, MessageType
from smart_home_automation.common.framing import decode_message
from smart_home_automation.server.server import Server


def make_writer():
    writer = MagicMock()
    writer.drain = AsyncMock()
    return writer


class TestNodeErrorRouting(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = Server()
        self.node = make_writer()
        self.other_node = make_writer()

        self.server.state.register_node("room", [], [], self.node)
        self.server.state.register_node("other_room", [], [], self.other_node)

        self.panels = [make_writer(), make_writer()]
        for index, panel in enumerate(self.panels):
            self.server.state.register_panel(f"panel_{index}", "OWNER", panel)

        self.error = {
            "type": MessageType.ERROR,
            "code": ErrorCode.EXECUTION_FAILED,
            "message": "Fan could not start",
        }

    async def dispatch(self, writer, message=None):
        await self.server._dispatch_message(
            self.error if message is None else message,
            writer,
            ("127.0.0.1", 12345),
        )

    async def test_error_reaches_all_panels_with_node_id(self):
        before = self.server.state.system_state()

        await self.dispatch(self.node)

        for panel in self.panels:
            panel.write.assert_called_once()
            reply = decode_message(panel.write.call_args.args[0])
            self.assertEqual(
                reply,
                {
                    "type": MessageType.ERROR,
                    "code": ErrorCode.EXECUTION_FAILED,
                    "message": "Node room: Fan could not start",
                },
            )
            panel.drain.assert_awaited_once()

        self.node.write.assert_not_called()
        self.other_node.write.assert_not_called()
        self.assertEqual(self.server.state.system_state(), before)

    async def test_node_identity_comes_from_connection(self):
        message = self.error | {"node_id": "room"}

        await self.dispatch(self.other_node, message)

        for panel in self.panels:
            reply = decode_message(panel.write.call_args.args[0])
            self.assertEqual(
                reply["message"],
                "Node other_room: Fan could not start",
            )

    async def test_unknown_client_and_panel_errors_are_ignored(self):
        for sender in [make_writer(), self.panels[0]]:
            with self.subTest(sender=sender):
                await self.dispatch(sender)
                sender.write.assert_not_called()

        for panel in self.panels:
            panel.write.assert_not_called()

    async def test_disconnected_node_error_is_ignored(self):
        self.server.state.disconnect(self.node)

        await self.dispatch(self.node)

        for panel in self.panels:
            panel.write.assert_not_called()
        self.node.write.assert_not_called()

    async def test_broken_panel_does_not_block_other_panel(self):
        broken, healthy = self.panels
        broken.drain.side_effect = ConnectionResetError()

        await self.dispatch(self.node)

        broken.close.assert_called_once()
        self.assertEqual(self.server.state.get_panel_connections(), [healthy])
        healthy.write.assert_called_once()
        healthy.drain.assert_awaited_once()
        reply = decode_message(healthy.write.call_args.args[0])
        self.assertEqual(reply["message"], "Node room: Fan could not start")

import pytest

from smart_home_automation.common.framing import decode_message, encode_message
from smart_home_automation.common.messages import ProtocolError


class TestFraming:
    def test_encode(self): # Test that the encode is converting the message to bytes and ends with a new line.
        message = {"type": "SYSTEM_STATE", "nodes": []}

        result = encode_message(message)

        assert isinstance(result, bytes)
        assert result.endswith(b"\n")
        assert decode_message(result) == message
        assert result[:-1] == b'{"type":"SYSTEM_STATE","nodes":[]}'

    def test_decode(self): #Check that the decode is converting the bytes back to a dictionary and validates the message.
        data = b'{"type": "SYSTEM_STATE", "nodes": []}\n'
        result = decode_message(data)

        assert result == {"type": "SYSTEM_STATE", "nodes": []}

    def test_invalid_json(self): # Check that the decode raises a ProtocolError when the input is not valid JSON.
        with pytest.raises(ProtocolError):
            decode_message(b"not valid json\n")
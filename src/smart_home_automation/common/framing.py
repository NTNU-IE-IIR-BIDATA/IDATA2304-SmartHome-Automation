import json
from .messages import validate_message, ProtocolError
from .constants import ErrorCode, MAX_MESSAGE_SIZE

def encode_message(message: dict) -> bytes:
    validate_message(message)
    bytestring = (json.dumps(dict) + "\n").encode("utf-8")
    return bytestring


def decode_message(bytestring) -> dict:
    if len(bytestring) > MAX_MESSAGE_SIZE:
        raise ProtocolError(ErrorCode.MALFORMED_JSON, "Message exceeds 64KiB limit")

    try:
        decoded = json.loads(bytestring.decode("utf-8").strip())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ProtocolError(ErrorCode.MALFORMED_JSON, str(e))

    if not isinstance(decoded):
        raise ProtocolError(ErrorCode.INVALID_SCHEMA, "Message must be a JSON object")
    validate_message(decoded)
    return decoded
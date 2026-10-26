import json

from .constants import ErrorCode, MAX_MESSAGE_SIZE
from .messages import ProtocolError, validate_message


def encode_message(message: dict) -> bytes:
    if not isinstance(message, dict):
        raise ProtocolError(ErrorCode.INVALID_SCHEMA, "Message must be a JSON object")

    validate_message(message)
    return (json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def decode_message(bytestring: bytes) -> dict:
    if not isinstance(bytestring, (bytes, bytearray)):
        raise ProtocolError(ErrorCode.MALFORMED_JSON, "Message must be bytes")

    if len(bytestring) > MAX_MESSAGE_SIZE:
        raise ProtocolError(ErrorCode.MALFORMED_JSON, "Message exceeds 64KiB limit")

    try:
        text = bytes(bytestring).decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ProtocolError(ErrorCode.MALFORMED_JSON, str(exc)) from exc

    if not text:
        raise ProtocolError(ErrorCode.MALFORMED_JSON, "Message is empty")

    try:
        decoded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProtocolError(ErrorCode.MALFORMED_JSON, str(exc)) from exc

    if not isinstance(decoded, dict):
        raise ProtocolError(ErrorCode.INVALID_SCHEMA, "Message must be a JSON object")

    validate_message(decoded)
    return decoded
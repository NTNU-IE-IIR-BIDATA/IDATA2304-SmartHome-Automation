
from .constants import MessageType, ErrorCode

MESSAGE_SCHEMAS = {
    MessageType.REGISTER_NODE: {
        "node_id": str,
        "sensors": list,
        "actuators": list,
    },

    MessageType.REGISTER_PANEL: {
        "client_id": str,
        "role": str,
    },

    MessageType.SYSTEM_STATE: {
        "nodes": list,
    },

    MessageType.SENSOR_DATA: {
        "node_id": str,
        "sensor_id": str,
        "value": (int, float, str, bool),
        "unit": str,
        "timestamp": (int, float),
    },

    MessageType.ACTUATOR_CMD: {
        "target_node_id": str,
        "actuator_id": str,
        "command": str,
        "value": (int, float, type(None)),
    },

    MessageType.ACTUATOR_STATE: {
        "node_id": str,
        "actuator_id": str,
        "state": str,
        "success": bool,
    },

    MessageType.ERROR: {
        "code": str,
        "message": str,
    },
}

class ProtocolError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

def validate_message(message: dict):
    if "type" not in message:
        raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Missing required field: type")

    msg_type = message.get("type")

    schema = MESSAGE_SCHEMAS.get(msg_type)

    if schema is None:
        raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"No schema defined for message type: {msg_type}")

    for field_name, expected_type in schema.items():
        if field_name not in message:
            raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Missing required field: {field_name}")

        actual_value = message[field_name]
        if not isinstance(actual_value, expected_type):
            raise ProtocolError(
                ErrorCode.INVALID_SCHEMA,
                f"Invalid type for field {field_name}: expected {expected_type}, got {type(actual_value)}")

def create_error_message(code: ErrorCode, message: str) -> dict:
    return {
        "type": MessageType.ERROR,
        "code": str(code),
        "message": message
    }
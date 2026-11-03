import pytest

from smart_home_automation.common.constants import ErrorCode, MessageType
from smart_home_automation.common.messages import ProtocolError, validate_message

VALID_MESSAGES = [
    {
        "type": MessageType.REGISTER_NODE,
        "node_id": "living_room_01",
        "sensors": [
            {"id": "temp_1", "type": "temperature", "unit": "celsius"},
        ],
        "actuators": [
            {"id": "fan_1", "type": "fan", "state": "OFF"},
        ],
    },
    {
        "type": MessageType.REGISTER_PANEL,
        "client_id": "panel_mobile_01",
        "role": "OWNER",
    },
    {
        "type": MessageType.SYSTEM_STATE,
        "nodes": [],
    },
    {
        "type": MessageType.SENSOR_DATA,
        "node_id": "living_room_01",
        "sensor_id": "temp_1",
        "value": 22.5,
        "unit": "celsius",
        "timestamp": 1776686400,
    },
    {
        "type": MessageType.ACTUATOR_CMD,
        "target_node_id": "living_room_01",
        "actuator_id": "fan_1",
        "command": "ON",
        "value": None,
    },
    {
        "type": MessageType.ACTUATOR_STATE,
        "node_id": "living_room_01",
        "actuator_id": "fan_1",
        "state": "ON",
        "success": True,
    },
    {
        "type": MessageType.ERROR,
        "code": "ERR_ACTUATOR_NOT_FOUND",
        "message": "Actuator fan_99 does not exist.",
    },
]


# Every supported protocol message type should pass the schema validation.
@pytest.mark.parametrize("message", VALID_MESSAGES)
def test_valid_message_is_accepted(message):
    assert validate_message(message) is None


# A message without a valid type is invalid.
def test_missing_type_is_rejected():
    with pytest.raises(ProtocolError, match="type") as error:
        validate_message({"node_id": "living_room_01"})

    assert error.value.code == ErrorCode.INVALID_SCHEMA


# Message types outside the protocol specification are rejected.
def test_unknown_message_type_is_rejected():
    with pytest.raises(ProtocolError, match="UNKNOWN_MESSAGE") as error:
        validate_message({"type": "UNKNOWN_MESSAGE"})

    assert error.value.code == ErrorCode.INVALID_SCHEMA


# Each protocol message must contain all its fields required by its schema.
@pytest.mark.parametrize(
    ("message", "missing_field"),
    [
        (
                {
                    "type": MessageType.REGISTER_PANEL,
                    "role": "OWNER",
                },
                "client_id",
        ),
        (
                {
                    "type": MessageType.SENSOR_DATA,
                    "node_id": "living_room_01",
                    "sensor_id": "temp_1",
                    "value": 22.5,
                    "unit": "celsius",
                },
                "timestamp",
        ),
    ],
)
def test_missing_required_field_is_rejected(message, missing_field):
    with pytest.raises(ProtocolError, match=missing_field) as error:
        validate_message(message)

    assert error.value.code == ErrorCode.INVALID_SCHEMA


# Required fields must contain values of the types defined by the schema.
@pytest.mark.parametrize(
    ("message", "invalid_field"),
    [
        (
                {
                    "type": MessageType.REGISTER_NODE,
                    "node_id": 123,
                    "sensors": [],
                    "actuators": [],
                },
                "node_id",
        ),
        (
                {
                    "type": MessageType.ACTUATOR_STATE,
                    "node_id": "living_room_01",
                    "actuator_id": "fan_1",
                    "state": "ON",
                    "success": "yes",
                },
                "success",
        ),
        (
                {
                    "type": MessageType.SENSOR_DATA,
                    "node_id": "living_room_01",
                    "sensor_id": "temp_1",
                    "value": 22.5,
                    "unit": "celsius",
                    "timestamp": "not-a-timestamp",
                },
                "timestamp",
        ),
    ],
)
def test_invalid_field_type_is_rejected(message, invalid_field):
    with pytest.raises(ProtocolError, match=invalid_field) as error:
        validate_message(message)

    assert error.value.code == ErrorCode.INVALID_SCHEMA

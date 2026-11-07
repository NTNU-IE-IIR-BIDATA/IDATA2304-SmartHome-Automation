from enum import StrEnum

DEFAULT_PORT = 5555 # Default port for the smart home automation system
WILDCARD = "ALL" # Used to indicate all nodes or panels
MAX_MESSAGE_SIZE = 64 * 1024 # 64 KiB

class ErrorCode(StrEnum): #
    AUTH_FAILED = "ERR_AUTH_FAILED"
    MALFORMED_JSON = "ERR_MALFORMED_JSON"
    INVALID_SCHEMA = "ERR_INVALID_SCHEMA"
    NODE_NOT_FOUND = "ERR_NODE_NOT_FOUND"
    ACTUATOR_NOT_FOUND = "ERR_ACTUATOR_NOT_FOUND"
    EXECUTION_FAILED = "ERR_EXECUTION_FAILED"

class Role(StrEnum):
    ADMIN = "SHA_ADMIN"
    OWNER = "OWNER"
    GUEST = "GUEST"
    TECHNICIAN = "TECHNICIAN"

class MessageType(StrEnum):
    REGISTER_NODE = "REGISTER_NODE"
    REGISTER_PANEL = "REGISTER_PANEL"
    SYSTEM_STATE = "SYSTEM_STATE"
    SENSOR_DATA = "SENSOR_DATA"
    ACTUATOR_CMD = "ACTUATOR_CMD"
    ACTUATOR_STATE = "ACTUATOR_STATE"
    ERROR = "ERROR"

class ActuatorState(StrEnum):
    ON = "ON"
    OFF = "OFF"
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class SensorType(StrEnum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SMOKE = "smoke"
    AIR_QUALITY = "air_quality"
    POWER = "power"
    MOTION = "motion"
    LEAK = "leak"

class AnomalySeverity(StrEnum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AnomalyThresholdLabels(StrEnum):
    WARNING_MIN = "WARNING_MIN"
    WARNING_MAX = "WARNING_MAX"
    CRITICAL_MIN = "CRITICAL_MIN"
    CRITICAL_MAX = "CRITICAL_MAX"


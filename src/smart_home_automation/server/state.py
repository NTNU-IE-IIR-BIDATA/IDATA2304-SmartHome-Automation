from copy import deepcopy

from ..common.constants import ErrorCode, MessageType
from ..common.messages import ProtocolError

class ServerState:

    def __init__(self):
        self._nodes = {}
        self._connections = {}

    def register_node(self, node_id, sensors, actuators, connection):
        if not isinstance(node_id, str) or not node_id.strip() or node_id == "ALL":
            raise ProtocolError(ErrorCode.INVALID_SCHEMA, "Invalid or reserved node_id")
        if node_id in self._connections:
            raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Node {node_id} is already connected")
        if any(current is connection for current in self._connections.values()):
            raise ProtocolError(ErrorCode.INVALID_SCHEMA, "connection is already registered")
        self._validate_manifest(sensors, "sensor")
        self._validate_manifest(actuators, "actuator")
        self._nodes[node_id] = {
            "node_id": node_id,
            "connected": True,
            "sensors": deepcopy(sensors),
            "actuators": deepcopy(actuators),
        }
        self._connections[node_id] = connection

    @staticmethod
    def _validate_manifest(items, kind):
        if not isinstance(items, list):
            raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"{kind} manifest must be a list")
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Invalid {kind} entry")
            identifier = item.get("id")
            item_type = item.get("type")
            if not isinstance(identifier, str) or not identifier.strip() or identifier == "ALL":
                raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Invalid {kind} ID")
            if identifier in seen:
                raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Duplicate {kind} ID: {identifier}")
            if not isinstance(item_type, str) or not item_type.strip():
                raise ProtocolError(ErrorCode.INVALID_SCHEMA, f"Missing {kind} type")
            seen.add(identifier)

    def disconnect(self, connection):
        for node_id, current in list(self._connections.items()):
            if current is connection:
                del self._connections[node_id]
                self._nodes[node_id]["connected"] = False
                return node_id

    def get_node(self, node_id):
        return deepcopy(self._nodes.get(node_id))

    def get_connection(self, node_id):
        return self._connections.get(node_id)

    def system_state(self):
        return {"type": MessageType.SYSTEM_STATE, "nodes": deepcopy(list(self._nodes.values()))}
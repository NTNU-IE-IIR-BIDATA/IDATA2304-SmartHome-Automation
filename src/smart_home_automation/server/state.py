from copy import deepcopy

from ..common.constants import ErrorCode, MessageType
from ..common.messages import ProtocolError


class ServerState:

    def __init__(self):
        self._nodes = {}
        self._connections = {}
        self._panels = {}

    def register_panel(self, client_id, role, connection):
        if not isinstance(client_id, str) or not client_id.strip():
            raise ProtocolError(
                ErrorCode.INVALID_SCHEMA,
                "Invalid client_id"
            )

        if client_id in self._panels:
            raise ProtocolError(
                ErrorCode.INVALID_SCHEMA,
                "Panel is already registered"
            )

        if any(
            panel["connection"] is connection
            for panel in self._panels.values()
        ) or any (
            current is connection
            for current in self._connections.values()
        ):
            raise ProtocolError(
                ErrorCode.INVALID_SCHEMA,
                "Connection is already registered"
            )
        self._panels[client_id] = {
            "role": role,
            "connection": connection
        }

    def get_panel_connections(self):
        return [
            panel["connection"]
            for panel in self._panels.values()
        ]


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

        for client_id, panel in list(self._panels.items()):
            if panel["connection"] is connection:
                del self._panels[client_id]
                return client_id

        return None

    def get_node(self, node_id):
        return deepcopy(self._nodes.get(node_id))

    def get_connection(self, node_id):
        return self._connections.get(node_id)

    def get_sensor(self, node_id, sensor_id):
        node = self.get_node(node_id)
        if node is None:
            return None
        for sensor in node["sensors"]:
            if sensor.get("id") == sensor_id:
                return sensor
        return None

    def _find_sensor(self, node_id, sensor_id):
        node = self._nodes.get(node_id)
        if not node:
            return None
        for s in node["sensors"]:
            if s.get("id") == sensor_id:
                return s
        return None

    def system_state(self):
        return {"type": MessageType.SYSTEM_STATE, "nodes": deepcopy(list(self._nodes.values()))}

    def update_sensor_data(
            self,
            node_id,
            sensor_id,
            value,
            unit=None,
            timestamp=None,
            connection=None
    ):
        if node_id not in self._nodes:
            raise ProtocolError(ErrorCode.NODE_NOT_FOUND, f"Node {node_id} not found")

        if connection is None or connection is not self.get_connection(node_id):
            raise ProtocolError(ErrorCode.AUTH_FAILED, "Node id does not match connection")

        target_sensor = self._find_sensor(node_id, sensor_id)

        if target_sensor is None:
            raise ProtocolError(
                ErrorCode.INVALID_SCHEMA,
                f"Sensor {sensor_id} not found on node {node_id}"
            )

        target_sensor["value"] = value

        if unit is not None:
            target_sensor["unit"] = unit
        if timestamp is not None:
            target_sensor["timestamp"] = timestamp

# Smart Home Automation Protocol (SHAP) Specification

## 1. Introduction
This document describes the application-layer communication protocol Smart Home Automation Protocol (SHAP), 
designed for data exchange between sensor-actuator nodes, control-panel nodes, 
and a central server in a smart home environment.

## 2. Terminology

- **Server**: The central hub/middleman administering connections, routing messages, storing the current system state and handling client authorization levels
- **Sensor-Actuator-Node (SAN)**: A unit containing one or more sensors and/or actuators, operating as a TCP Client
- **Control Panel (CP)**: A user interface (client) used for the monitoring of sensor data and initiation of actuator commands
- **Framing**: The method used to limit individual messages over a continuous TCP byte stream
- **NDJSON (Newline-Delimited-JSON)**: Data format where each message consists of a valid JSON-Object encoded in UTF-8, ended by a newline (`\n`)
- **Telemetry**: Continuous or periodic sensor data values

## 3. Underlying Transport Protocol

SHAP exclusively uses the Transmission Control Protocol (TCP).

*Justification*: Actuator commands, such as door locking, fire alarm or heater adjustments require
reliability and sequential delivery. TCP eliminates the need to reimplement packet order, error detection and retransmission in the application layer, reducing the protocols complexity compared to UDP.

## 4. Port Number

Standard listening port for the SHAP server is ```5555/TCP```

*Justification*: Port `5555` lies within the dynamic/private port range, avoiding conflict with standardized privileged ports below 1024. The port may be overridden by configuration parameters during boot.


## 5. Overall architecture

### Actors

- ```Server```: Central hub. Handles TCP sessions, identification and role based authorization of control panels, message verification, storing the last known state of all nodes, and routing messages between nodes.
- ```Sensor nodes (SAN)```: Clients who initiates outgoing connections to the server, registers their units, send sensor data and listens for actuator commands.
- ```Control panels (CP)```: Clients who connects to the server, receiving real-time updates and sends commands based on access level

### Connection direction
All TCP connections are initiated from the clients (SAN and CP) against the server. There is no direct node-to-node communication.

*Justification*: Direct communication between nodes would require the nodes to serve multiple functionalities. Separating the nodes and sensors from the server simplifies synchronization and handling of multiple clients.

## 6. Information flow

The protocol relies on an asynchronous, event-driven push-model:

- **Registration:** Immediately after the TCP-connection is established, the clients send an instruction message (```REGISTER_NODE```or ```REGISTER_PANEL```)
- **Telemetry and state changes (SAN → Server):** Sensor nodes push data based on set intervals (for slow data such as temperature), or immediately for threshold/state-changes (movement, smoke). The node does not wait for explicit requests from the server
- **Broadcast (Server → CP):** When the server receives new data or state changes from a sensor node, the values are cached, and the message forwarded immediately to all connected control panels with access
- **Commands (CP → Server → SAN):** Control panels send actuator commands to the server. The server serialises the request, and routes the command to the specific sensor node via the established socket of the node
- **Confirmation (SAN → Server → CP):** The sensor node executes the action and sends a confirmation (`ACTUATOR_STATE`) back to the server, who updates the cache and notifies the control panels

*Justification*: A purely polling based system would introduce potentially unacceptable latency for critical alarms and generate unnecessary network traffic from static measurements.
A push based system minimizes bandwidth usage, and ensures an immediate response on updates.

## 7. Protocol type

**Connection oriented:** The protocol operates exclusively over persistent TCP-Streams. Breaks in the TCP-Session is regarded as disconnection of the node.

**Statefulness**: Stateful. The server actively maintains a state for each session: client type, client ID, authorization level for panels, and a list over related sensors and actuators. Clients need to register before other messages are accepted.

*Justification*: A stateful architecture is necessary for the server to know which TCP socket belongs to which node for command routing, as well as rejecting unauthorized actions without the need for full accreditation in every single measurement message.

## 8. Types, constants and special values

### Reserved identifiers
`ALL`: Used as wildcard in fields for `target_node_id` or `actuator_id` for joint commands (multicast/broadcast). 
Wildcard expansion is handled by the server. if `target_node` is `ALL`, the server iterates over all registered nodes and dispatches individual commands to each relevant socket.

### Roles and access levels (Control Panel)

- `SHA_ADMIN`: Full access to all nodes, sensors, actuators, rules and diagnostics
- `OWNER`: Full control of all units inside the building
- `GUEST`: Read-only access to chosen sensors, limited access to chosen actuators
- `TECHNICIAN`: Read-only access to diagnostics, resetting of alarms, no access to critical actuators (e.g. main door lock)

### Actuator states

- `ON`, `OFF`
- `OPEN`, `CLOSED`
- `VALUE`: Numerical value (e.g. humidity percentage, temperature)

### Error codes
- `ERR_AUTH_FAILED`: Invalid auth level or unknown client
- `ERR_MALFORMED_JSON`: Syntax error in transmitted JSON-string
- `ERR_INVALID_SCHEMA`: Required fields missing or contains wrong data type
- `ERR_NODE_NOT_FOUND`: Target node not connected/does not exist
- `ERR_ACTUATOR_NOT_FOUND`: Requested actuator does not exist on the node
- `ERR_EXECUTION_FAILED`: Hardware/actuator error on the sensor node

## 9. Message format and catalog

### Framing

The protocol uses Line-Delimited JSON (NDJSON) encoded in UTF-8. Every message is formatted on exactly one line, ended by line-shift (`\n`).

*Justification*: JSON gives a structural flexibility and makes the protocol independent of any programming language, as well as making it easily expandable for new sensor types. 
Limiting with `\n` removes the need for a separate binary length header, allowing parsing via standard I/O functions.

### Common structure

All messages must contain the `type` field.

### Message catalog

#### Sensor node registration: `REGISTER_NODE`

**Direction**: SAN → Server

**Description**: First message from a connected sensor node

```JSON
{
  "type": "REGISTER_NODE",
  "node_id": "living_room_01",
  "sensors": [
    {"id": "temp_1", "type": "temperature", "unit": "celsius"},
    {"id": "hum_1", "type": "humidity", "unit": "percent"}
  ],
  "actuators": [
    {"id": "fan_1", "type": "fan", "state": "OFF"}
  ]
}
```

#### Control Panel Registration: `REGISTER_PANEL`

**Direction**: CP → Server

**Description**: First message from a connected control panel

```JSON
{
  "type": "REGISTER_PANEL",
  "client_id": "panel_mobile_01",
  "role": "OWNER"
}
```

#### Initial system state: `SYSTEM_STATE`

**Direction**: Server → CP

**Description**: Sent from server immediately after a control panel is successfully connected. Contains a full overview of connected nodes and their states.

```JSON
{
  "type": "SYSTEM_STATE",
  "nodes": [
    {
      "node_id": "living_room_01",
      "connected": true,
      "sensors": [
        {"id": "temp_1", "type": "temperature", "value": 22.4, "unit": "celsius"}
      ],
      "actuators": [
        {"id": "fan_1", "type": "fan", "state": "OFF"}
      ]
    }
  ]
}
```

#### Sensor Data: `SENSOR_DATA`

**Direction**: SAN → Server, then forwarded to Server → CP

**Description**: Transfer of telemetry values

```JSON
{
  "type": "SENSOR_DATA",
  "node_id": "living_room_01",
  "sensor_id": "temp_1",
  "value": 22.5,
  "unit": "celsius",
  "timestamp": 1776686400
}
```

#### Actuator commands: `ACTUATOR_CMD`

**Direction**: CP → Server, then forwarded to Server → SAN

**Description**: Command for change of actuator status. Supports specific unit or wildcard.

```JSON
{
  "type": "ACTUATOR_CMD",
  "target_node_id": "living_room_01",
  "actuator_id": "fan_1",
  "command": "ON",
  "value": null
}
```

#### Actuator state update: `ACTUATOR_STATE`

**Direction**: SAN → Server, then forward to Server → CP.

**Description**: Confirmation that the actuator state actually changed.

```JSON
{
  "type": "ACTUATOR_STATE",
  "node_id": "living_room_01",
  "actuator_id": "fan_1",
  "state": "ON",
  "success": true
}
```

#### Error message: `ERROR`

**Direction**: Server → Client (CP or SAN).

**Description**: Reporting breaches of protocol rules.

```JSON
{
  "type": "ERROR",
  "code": "ERR_ACTUATOR_NOT_FOUND",
  "message": "Actuator fan_99 does not exist on node living_room_01."
}
```

## 10. Error handling

- **Invalid JSON**: If the recipient cannot parse the line as valid JSON, `ERR_MALFORMED_JSON` is returned. If something continues to transmit invalid data, the server sends the error message, flushes the socket buffer and terminates the TCP session.
- **Unknown or missing fields**: Not silently ignored. The recipient returns `ERR_INVALID_SCHEMA`, specifying which field was missing or invalid.
- **Unreachable target node**: If a panel sends `ACTUATOR_CMD` to a node which is not registered or recently disconnected, the server returns `ERR_NODE_NOT_FOUND` to the panel.
- **Unauthorized operation**: If a control panel with the role `GUEST` tries to perform an action reserved for `OWNER`, the server rejects the request with `ERR_AUTH_FAILED` without forwarding it to the sensor node

## 11. Example Scenario

**Scenario: Automatic and manual temperature control in the living room**:

1. `SAN` (living room) initiates a TCP connection to `Server`and sends `REGISTER_NODE`
2. `CP` (house owner) connects and sends `REGISTER_PANEL` with role `OWNER`
3. `Server` sends out `SYSTEM_STATE` status update to the panel, which visualizes the living room node with a temperature of $24.0^\circ\text{C}$ and fan `OFF`
4. The living room node registers a temperature increase to $25.5^\circ\text{C}$, and sends `SENSOR_DATA` to the server
5. `Server` updates its state table, sending `SENSOR_DATA`forward to the panel, updating its visualization
6. The user presses the "Start fan" button. The panel sends:

    ```{"type": "ACTUATOR_CMD", "target_node_id": "living_room_01", "actuator_id": "fan_1", "command": "ON"}```
7. `Server` verifies that `OWNER` has the necessary permissions for the action, and forwards the message via the TCP connection to `living_room_01`
8. The node starts the physical/simulated fan, updates its internal state and responds to the server with:

    ```{"type": "ACTUATOR_STATE", "node_id": "living_room_01", "actuator_id": "fan_1", "state": "ON", "success": true}```
9. `Server` stores the new state and forwards `ACTUATOR_STATE` to the control panel, changing its status indicator to green/active


## 12. Reliability mechanisms

**TCP Enforcing**: TCP guarantees reliable byte stream delivery for established connections, 
with packet loss detection  and automatic retransmissions handled by the transport layer.

**State monitoring**: The server notices closed TCP-streams immediately. 
If a sensor node loses connection, the server marks the node `connected: false` and sends out a status to all control panels.

**Client reconnect**: Both sensor and control panels implement automatic reconnection if the TCP connection breaks.

## 13. Security mechanisms

**Role-based access control**: The server functions as an authorization service based on the role given under registration (`SHA_ADMIN`, `OWNER`, `GUEST`, `TECHNICIAN`)

**Data sanity checks**: The server validates that command and ID strings are alphanumerical to prevent injection attacks or state interruptions.

## 14. Assumptions

**Network environment**: The server has a known or static IP-address and listens to port `5555`. The clients know this address on startup.

**Unique ID's**: Every sensor node is configured with a unique ID string on startup. The server rejects connection requests if a node attempts to register with an already active `node_id`.

**Message size**: No single-line-JSON should exceed 64KiB to avoid memory overload by parsing in buffer. 

**Anomaly detection**: Control panels evaluate incoming data against known threshold rules (e.g. temperatures exceeding an unsafe limit) to trigger anomaly warnings in the user interface.

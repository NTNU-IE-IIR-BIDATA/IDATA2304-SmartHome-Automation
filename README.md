# Smart Home Automation

An IDATA2304 group project that implements a smart-home system with simulated sensor-actuator nodes, a central TCP server, and a Textual control panel.

## Overview

The system has three parts:

1. **Server** - accepts connections, keeps track of node and sensor state, checks panel permissions, routes actuator commands, and forwards updates.
2. **Sensor-actuator node** - registers sensors and actuators, sends sensor readings every 5 seconds, and runs actuator commands from the server.
3. **Control panel** - terminal UI showing connected nodes, live sensor readings, anomaly warnings, and an input bar for actuator commands.

Nodes and control panels talk to the server using the Smart Home Automation Protocol (SHAP), which sends newline-delimited JSON messages over TCP. The default address is `127.0.0.1:5555`, and the server also listens on UDP port `5556` for automatic discovery. See [protocol.md](protocol.md) for the full specification.

Sprint reports can be found in [sprint_reports.md](sprint_reports.md).

### How messages flow

1. A node connects to the server and sends its sensor/actuator manifest (`REGISTER_NODE`).
2. The node pushes sensor readings every 5 seconds (`SENSOR_DATA`).
3. A control panel connects (`REGISTER_PANEL`) and gets the current `SYSTEM_STATE`.
4. New sensor readings and actuator updates are forwarded to all connected control panels.
5. When a user enters a command, the server checks the panel's role and forwards `ACTUATOR_CMD` to the target node(s).
6. The node runs the command and replies with `ACTUATOR_STATE`, which is broadcast back to the control panels.

If a connection drops, nodes automatically retry with backoff, and the control panel tries to reconnect a few times before stopping. On the server side, malformed messages return an `ERROR` response, and repeated protocol errors close the connection.

## Requirements

- Python 3.15 (set in `pyproject.toml`)
- `uv` ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- A terminal with UTF-8 and color support for the Textual UI

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/NTNU-IE-IIR-BIDATA/IDATA2304-SmartHome-Automation.git
cd IDATA2304-SmartHome-Automation
uv sync
```

## Quick start

Open three terminals in the project directory and use TLS for every
connection. The repository includes demo certificates so no certificate
generation is needed for the exam setup:

Terminal 1 (server):

```bash
uv run server --cert-file tls/demo/server.crt --key-file tls/demo/server.key
```

Terminal 2 (example node):

```bash
uv run node --id living_room_01 --ca-file tls/demo/ca.crt --sensor temperature:temp_1 --sensor humidity:humidity_1 --actuator fan:fan_1
```

Terminal 3 (control panel):

```bash
uv run control_panel --ca-file tls/demo/ca.crt
```

The files in `tls/demo` are intentionally included demo keys for this exam
project. They must be replaced with newly generated CA and server certificates
and private keys before deploying the application anywhere.

## Running each component

### Server

```bash
uv run server --cert-file tls/demo/server.crt --key-file tls/demo/server.key \
  [--host HOST] [--port PORT]
```

The server defaults to host `127.0.0.1` on port `5555`, and also listens on UDP port `5556` for server discovery. But you can use another host and port (use `0.0.0.0` if clients on other machines should connect or discover it):

```bash
uv run server --host 0.0.0.0 --port 5555 \
  --cert-file tls/demo/server.crt --key-file tls/demo/server.key
```

### Sensor-actuator node

A node needs a unique `--id` and at least one `--sensor` or `--actuator` in `TYPE:ID` format. Both flags can be passed multiple times.

```bash
uv run node --id NODE_ID \
  --ca-file tls/demo/ca.crt \
  --sensor TYPE:ID \
  --actuator TYPE:ID \
  [--host HOST] [--port PORT] [--discover]
```

`--host` (or `--ip`) and `--port` default to `127.0.0.1` and `5555`.
`--discover` finds the server automatically over UDP (port `5556`) instead of using `--host` and `--port`, exiting if no server responds within 3 seconds.
`--ca-file` verifies the server certificate and is required for the documented
TLS startup.

Supported sensor types: `temperature`, `humidity`, `smoke`, `air_quality`, `power`, `motion`, `leak`

Supported actuator types: `fan`, `heater`, `lock`

Run `uv run node --help` to see all options.

### Control panel

```bash
uv run control_panel [--id PANEL_ID] [--role ROLE] [--host HOST] [--port PORT] \
  [--discover] --ca-file tls/demo/ca.crt
```

By default, it connects to `127.0.0.1:5555` as `panel_1` with role `OWNER`.
`--discover` finds the server automatically over UDP (port `5556`) instead of using `--host` and `--port`, exiting if no server responds within 3 seconds.
`--ca-file` verifies the server certificate and is required for the documented
TLS startup.

Available roles:

- `SHA_ADMIN` / `OWNER`: can send all actuator commands
- `GUEST`: can only send `ON` / `OFF` to `fan` actuators
- `TECHNICIAN`: read-only monitoring (cannot control actuators)

The anomaly feed flags out-of-range readings (for example high/low temperature, humidity, power, air quality, or triggered `smoke`/`leak` sensors) as `WARNING` or `CRITICAL`.

To control an actuator, type a command in the bottom input box:

```text
<node_id|ALL> <actuator_id|ALL> <command>
```

You can also prefix commands with `set` or `cmd`, and use `ALL` to target every connected node or every actuator on a node:

```text
living_room_01 fan_1 ON
living_room_01 ALL OFF
ALL fan_1 ON
```

Valid commands by actuator type:

- `fan`, `heater`: `ON`, `OFF`
- `lock`: `OPEN`, `CLOSED`

Shortcuts: `q` quits the panel, `c` clears the anomaly feed.

## Testing and linting

Run tests:

```bash
uv run pytest
```

Run the linter:

```bash
uv run ruff check
```

## Project structure

```text
src/
├── smart_home_automation/
│   ├── common/                 Shared constants, framing, discovery, TLS, and message validation
│   ├── server/                 TCP server and system state
│   ├── node/                   Simulated sensors, actuators, and node client
│   └── control_panel/          Control-panel client, anomaly detector, and Textual UI
└── tests/                      Unit and integration tests
protocol.md                     SHAP protocol specification
pyproject.toml                  Project metadata, scripts, and dependencies
```

# Smart Home Automation

An IDATA2304 project that implements a small smart-home system. The
application uses an asynchronous TCP server to connect sensor and actuator nodes
to a Textual control panel.

## What this project does

The system has three parts:

1. **Server** – central hub that accepts connections, stores the latest system
   state, routes actuator commands, and broadcasts updates.
2. **Sensor-actuator node** – client that registers sensors and actuators,
   periodically sends sensor readings, and executes actuator commands.
3. **Control panel** – terminal user interface that displays sensor data,
   reports anomalies, and sends actuator commands.

Communication uses the Smart Home Automation Protocol (SHAP): newline-delimited
JSON messages over TCP. The default server address is `127.0.0.1:5555`.
See [protocol.md](protocol.md) for the complete protocol specification.

## Requirements

- Python 3.15
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- A terminal that supports the Textual control panel

The required Python version is defined in `pyproject.toml`.

## Installation

Clone the repository and move into the project directory:

```console
git clone https://github.com/NTNU-IE-IIR-BIDATA/IDATA2304-SmartHome-Automation.git
cd IDATA2304-SmartHome-Automation
```

Install Python 3.15 if needed, then create the project environment and install
dependencies:

```console
uv python install 3.15
uv sync
```

## Running the application

Start each component in its own terminal, from the project directory.

### 1. Start the server

```console
uv run server
```

The server listens on `127.0.0.1:5555` by default.

### 2. Start a sensor-actuator node

Provide a unique node ID and at least one sensor or actuator. Components use
the format `TYPE:ID`:

```console
uv run node --id ID 
  --host 192.168.1.25
  --port 6000
  --sensor TYPE:ID
  --actuator TYPE:ID
```

`--host` (also available as `--ip`) and `--port` select the server address.
They default to `127.0.0.1` and `5555` when omitted.

Available sensor types:

`temperature`, `humidity`, `smoke`, `air_quality`, `power`, `motion`, `leak`

Available actuator types:

`fan`, `heater`, `lock`

Both `--sensor` and `--actuator` can be repeated. 

Example:

```console
uv run node --id living_room_01 
  --sensor temperature:temp_1 
  --sensor humidity:humidity_1 
  --actuator fan:fan_1
```

Run `uv run node --help` to see all command-line options.

### 3. Start the control panel

```console
uv run control_panel
```

The control panel connects as `panel_1` with the `OWNER` role. It displays
connected sensors and actuators and includes an anomaly feed.

To send an actuator command, enter the following in the command field:

```text
<node_id> <actuator_id> <command> [value]
```

Example:

```text
living_room_01 fan_1 ON
```

Supported commands include `ON`, `OFF`, `OPEN`, and `CLOSED`, depending on the
actuator. Press `q` to quit the control panel and `c` to clear the anomaly
feed.

## Testing and code quality

Run the tests:

```console
uv run pytest
```

Run the linter:

```console
uv run ruff check
```

## Project structure

```text
src/
├── smart_home_automation/
│   ├── common/                 Shared constants, framing, and messages
│   ├── server/                 TCP server and system state
│   ├── node/                   Sensors, actuators, and node client
│   └── control_panel/          Control-panel client and Textual UI
└── tests/                      Unit and integration tests
protocol.md                    SHAP protocol specification
pyproject.toml                 Project metadata and dependencies
```

## How messages flow

1. A node connects to the server and sends its sensor/actuator manifest.
2. The node sends sensor readings approximately every five seconds.
3. The control panel connects and receives the current system state.
4. Sensor and actuator updates are forwarded to connected control panels.
5. A control-panel command is validated by the server and forwarded to the
   target node.
6. The node executes the command and sends an actuator-state confirmation.

All messages are UTF-8 encoded JSON objects terminated by a newline. The
server rejects malformed messages and closes a connection after repeated
protocol errors.


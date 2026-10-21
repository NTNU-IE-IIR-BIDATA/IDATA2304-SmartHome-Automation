# IDATA2304-SmartHome-Automation
Custom application-layer protocol and network implementation for a Smart Home Automation system – IDATA2304 project at NTNU

## Installation

note: fix this to be platform independent
```console
brew install uv
uv python install 3.15
uv venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows
```

## How to run

```console
uv run server
```

```console
uv run sensor
```

```console
uv run control_panel
```

```console
uv run pytest
```

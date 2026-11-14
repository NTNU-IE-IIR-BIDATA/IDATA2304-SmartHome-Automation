from .client import ControlPanelClient
from .ui import ControlPanelApp


def main() -> None:
    client = ControlPanelClient(
        client_id="panel_1",
        role="OWNER",
    )
    app = ControlPanelApp(client=client)
    app.run()


if __name__ == "__main__":
    main()

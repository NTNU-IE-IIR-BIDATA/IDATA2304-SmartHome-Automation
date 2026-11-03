from dataclasses import dataclass


@dataclass
class Sensor:
    """A sensor description used in a SAN registration manifest."""

    id: str
    type: str
    unit: str

    def manifest(self) -> dict[str, str]:
        return {"id": self.id, "type": self.type, "unit": self.unit}


class TemperatureSensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, "temperature", "celsius")


class HumiditySensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, "humidity", "percent")


class DoorSensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, "door", "state")


def create_sensor(sensor_type: str, sensor_id: str) -> Sensor:
    sensors = {
        "temperature": TemperatureSensor,
        "humidity": HumiditySensor,
        "door": DoorSensor,
    }
    try:
        sensor_class = sensors[sensor_type.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported sensor type: {sensor_type}") from error
    return sensor_class(sensor_id)

import random
from dataclasses import dataclass

from smart_home_automation.common.constants import SensorType


@dataclass
class Sensor:
    """A sensor description used in a SAN registration manifest."""

    id: str
    type: str
    unit: str

    def __init__(self, sensor_id: str, sensor_type: str, sensor_unit: str) -> None:
        self.id = sensor_id
        self.type = sensor_type
        self.unit = sensor_unit


    def manifest(self) -> dict[str, str]:
        return {"id": self.id, "type": self.type, "unit": self.unit}

    def read_value(self) -> float | str | int | bool:
        """Return the current simulated sensor value."""
        ...


def _bounded_variation(value: float, minimum: float, maximum: float, step: float) -> float:
    """Return a realistic next reading without leaving the sensor's range."""
    next_value = value + random.uniform(-step, step)
    return max(minimum, min(maximum, next_value))



class TemperatureSensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.TEMPERATURE.value, "celsius")
        self._value = 21.0

    def read_value(self) -> float:
        self._value = _bounded_variation(self._value, 5.0, 35.0, 0.1)
        return round(self._value, 1)


class HumiditySensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.HUMIDITY.value, "percent")
        self._value = 45.0

    def read_value(self) -> float:
        self._value = _bounded_variation(self._value, 0.0, 100.0, 2.0)
        return round(self._value, 1)


class SmokeDetector(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.SMOKE.value, "boolean")

    def read_value(self) -> bool:
        return random.random() < 0.01


class AirQualitySensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.AIR_QUALITY.value, "aqi")
        self._value = 35.0

    def read_value(self) -> float:
        self._value = _bounded_variation(self._value, 0.0, 500.0, 15.0)
        return round(self._value, 1)


class PowerSensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.POWER.value, "watts")
        self._value = 900.0

    def read_value(self) -> float:
        self._value = _bounded_variation(self._value, 100.0, 15000.0, 250.0)
        return round(self._value, 1)


class MotionSensor(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.MOTION.value, "boolean")

    def read_value(self) -> bool:
        return random.random() < 0.05


class LeakDetector(Sensor):
    def __init__(self, sensor_id: str) -> None:
        Sensor.__init__(self, sensor_id, SensorType.LEAK.value, "boolean")

    def read_value(self) -> bool:
        return random.random() < 0.01



def create_sensor(sensor_type: str, sensor_id: str) -> Sensor:
    sensors = {
        SensorType.TEMPERATURE.value: TemperatureSensor,
        SensorType.HUMIDITY.value: HumiditySensor,
        SensorType.SMOKE.value: SmokeDetector,
        SensorType.AIR_QUALITY.value: AirQualitySensor,
        SensorType.POWER.value: PowerSensor,
        SensorType.MOTION.value: MotionSensor,
        SensorType.LEAK.value: LeakDetector,
    }
    try:
        sensor_class = sensors[sensor_type.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported sensor type: {sensor_type}") from error
    return sensor_class(sensor_id)

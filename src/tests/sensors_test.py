import pytest

from smart_home_automation.common.constants import SensorType
from smart_home_automation.node.sensors import (
    AirQualitySensor,
    HumiditySensor,
    LeakDetector,
    MotionSensor,
    PowerSensor,
    SmokeDetector,
    TemperatureSensor,
    create_sensor,
)


def test_sensor_manifests():
    assert TemperatureSensor("temp_1").manifest() == {
        "id": "temp_1",
        "type": SensorType.TEMPERATURE.value,
        "unit": "celsius",
    }
    assert HumiditySensor("hum_1").manifest()["unit"] == "percent"


@pytest.mark.parametrize(
    ("sensor_type", "sensor_class", "unit", "value_type"),
    [
        (SensorType.TEMPERATURE.value, TemperatureSensor, "celsius", float),
        (SensorType.HUMIDITY.value, HumiditySensor, "percent", float),
        (SensorType.SMOKE.value, SmokeDetector, "boolean", bool),
        (SensorType.AIR_QUALITY.value, AirQualitySensor, "aqi", float),
        (SensorType.POWER.value, PowerSensor, "watts", float),
        (SensorType.MOTION.value, MotionSensor, "boolean", bool),
        (SensorType.LEAK.value, LeakDetector, "boolean", bool),
    ],
)
def test_simulated_sensors_have_valid_manifests_and_values(
    sensor_type,
    sensor_class,
    unit,
    value_type,
):
    sensor = create_sensor(sensor_type, f"{sensor_type}_1")

    assert isinstance(sensor, sensor_class)
    assert sensor.manifest() == {
        "id": f"{sensor_type}_1",
        "type": sensor_type,
        "unit": unit,
    }
    assert isinstance(sensor.read_value(), value_type)


def test_numeric_sensor_values_stay_in_realistic_ranges():
    temperature = TemperatureSensor("temp_1")
    humidity = HumiditySensor("hum_1")
    air_quality = AirQualitySensor("air_quality_1")
    power = PowerSensor("power_1")

    for _ in range(100):
        assert 5.0 <= temperature.read_value() <= 35.0
        assert 0.0 <= humidity.read_value() <= 100.0
        assert 0.0 <= air_quality.read_value() <= 500.0
        assert 100.0 <= power.read_value() <= 15000.0


@pytest.mark.parametrize("sensor_class", [SmokeDetector, MotionSensor, LeakDetector])
def test_detector_sensors_return_boolean_values(sensor_class):
    sensor = sensor_class("detector_1")

    for _ in range(100):
        assert isinstance(sensor.read_value(), bool)


def test_unknown_sensor_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        create_sensor("unknown", "sensor_1")

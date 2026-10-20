from src.sensor.SensorInterface import SensorInterface


class WaterSensor(SensorInterface):
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.is_water = False

    @property
    def sensor_id(self):
        return self.sensor_id

    @property
    def sensor_type(self) -> str:
        return "Water"

    def get_data(self) -> dict:
        return {"water": self.is_water}

    def tick(self) -> None:
        pass
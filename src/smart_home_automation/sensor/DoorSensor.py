from src.sensor.SensorInterface import SensorInterface


class DoorSensor(SensorInterface):
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.is_open = False

    @property
    def sensor_id(self):
        return self.sensor_id

    @property
    def sensor_type(self) -> str:
        return "Door"

    def get_data(self) -> dict:
        return {"open": self.is_open}

    def tick(self) -> None:
        pass
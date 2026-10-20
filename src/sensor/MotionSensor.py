from src.sensor.SensorInterface import SensorInterface


class MotionSensor(SensorInterface):
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.motion_detected = False

    @property
    def sensor_id(self):
        return self.sensor_id

    @property
    def sensor_type(self) -> str:
        return "Motion"

    def get_data(self) -> dict:
        return {"motion": self.motion_detected}

    def tick(self) -> None:
        pass
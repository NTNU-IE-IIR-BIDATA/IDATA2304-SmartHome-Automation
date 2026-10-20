from src.sensor.SensorInterface import SensorInterface

class TemperatureSensor(SensorInterface):

    def __init__(self, sensor_id, current_temperature):
        self.sensor_id = sensor_id
        self.current_temperature = current_temperature

    @property
    def sensor_id(self) -> str:
        return self.sensor_id

    @property
    def sensor_type(self) -> str:
        return "temperature"

    def get_data(self) -> dict:
        return {"temperature": self.current_temperature}

    def set_temperature(self, temperature):
        self.current_temperature = temperature

    def tick(self) -> None:
        pass
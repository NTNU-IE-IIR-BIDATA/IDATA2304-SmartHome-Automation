from SensorInterface import SensorInterface

class TemperatureSensor(SensorInterface):

    def __init__(self):
        self.current_temperature = 20

    def set_temperature(self, temperature):
        self.current_temperature = temperature

    def get_data(self) -> dict:
        return {float: self.current_temperature}

    def tick(self) -> None:
        pass
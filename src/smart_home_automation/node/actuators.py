from dataclasses import dataclass

from smart_home_automation.common.constants import ActuatorState


@dataclass
class Actuator:
    """An actuator description used in a SAN registration manifest."""

    id: str
    type: str
    state: ActuatorState

    def manifest(self) -> dict[str, str]:
        return {"id": self.id, "type": self.type, "state": self.state.value}


class FanActuator(Actuator):
    def __init__(self, actuator_id: str) -> None:
        Actuator.__init__(self, actuator_id, "fan", ActuatorState.OFF)


class HeaterActuator(Actuator):
    def __init__(self, actuator_id: str) -> None:
        Actuator.__init__(self, actuator_id, "heater", ActuatorState.OFF)


class LockActuator(Actuator):
    def __init__(self, actuator_id: str) -> None:
        Actuator.__init__(self, actuator_id, "lock", ActuatorState.CLOSED)


def create_actuator(actuator_type: str, actuator_id: str) -> Actuator:
    actuators = {
        "fan": FanActuator,
        "heater": HeaterActuator,
        "lock": LockActuator,
    }
    try:
        actuator_class = actuators[actuator_type.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported actuator type: {actuator_type}") from error
    return actuator_class(actuator_id)
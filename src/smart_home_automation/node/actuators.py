from dataclasses import dataclass

from smart_home_automation.common.constants import ActuatorState, ActuatorType


@dataclass
class Actuator:
    """An actuator description used in a SAN registration manifest."""

    id: str
    type: str
    state: ActuatorState

    def __init__(self, actuator_id: str, actuator_type: str, actuator_state: ActuatorState):
        self.id = actuator_id
        self.type = actuator_type
        self.state = actuator_state

    def manifest(self) -> dict[str, str]:
        return {"id": self.id, "type": self.type, "state": self.state.value}

    def execute(self, command: str, value: float | int | None = None) -> bool:
        """Apply a supported command and return whether it was accepted."""
        allowed_states = {
            ActuatorType.FAN.value: {ActuatorState.ON, ActuatorState.OFF},
            ActuatorType.HEATER.value: {ActuatorState.ON, ActuatorState.OFF},
            ActuatorType.LOCK.value: {ActuatorState.OPEN, ActuatorState.CLOSED},
        }
        try:
            new_state = ActuatorState(command.upper())
        except (AttributeError, ValueError):
            return False

        if new_state not in allowed_states.get(self.type, set()):
            return False

        self.state = new_state
        return True


class FanActuator(Actuator):
    def __init__(self, actuator_id: str) -> None:
        super().__init__(actuator_id, ActuatorType.FAN.value, ActuatorState.OFF)


class HeaterActuator(Actuator):
    def __init__(self, actuator_id: str) -> None:
        super().__init__(actuator_id, ActuatorType.HEATER.value, ActuatorState.OFF)


class LockActuator(Actuator):
    def __init__(self, actuator_id: str) -> None:
        super().__init__(actuator_id, ActuatorType.LOCK.value, ActuatorState.CLOSED)


def create_actuator(actuator_type: str, actuator_id: str) -> Actuator:
    actuators = {
        ActuatorType.FAN.value: FanActuator,
        ActuatorType.HEATER.value: HeaterActuator,
        ActuatorType.LOCK.value: LockActuator,
    }
    try:
        actuator_class = actuators[actuator_type.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported actuator type: {actuator_type}") from error
    return actuator_class(actuator_id)

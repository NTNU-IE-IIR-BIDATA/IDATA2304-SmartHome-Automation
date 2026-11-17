import pytest

from smart_home_automation.common.constants import ActuatorState, ActuatorType
from smart_home_automation.node.actuators import (
    FanActuator,
    HeaterActuator,
    LockActuator,
    create_actuator,
)


def test_actuator_manifests():
    assert FanActuator("fan_1").manifest()["state"] == ActuatorState.OFF.value
    assert HeaterActuator("heater_1").manifest()["state"] == ActuatorState.OFF.value
    assert LockActuator("lock_1").manifest()["state"] == ActuatorState.CLOSED.value
    assert create_actuator(ActuatorType.LOCK.value.upper(), "lock_2").state == ActuatorState.CLOSED


@pytest.mark.parametrize(
    ("actuator", "command", "expected_state"),
    [
        (FanActuator("fan_1"), ActuatorState.ON, ActuatorState.ON),
        (FanActuator("fan_1"), ActuatorState.OFF, ActuatorState.OFF),
        (HeaterActuator("heater_1"), ActuatorState.ON, ActuatorState.ON),
        (HeaterActuator("heater_1"), ActuatorState.OFF, ActuatorState.OFF),
        (LockActuator("lock_1"), ActuatorState.OPEN, ActuatorState.OPEN),
        (LockActuator("lock_1"), ActuatorState.CLOSED, ActuatorState.CLOSED),
    ],
)
def test_execute_accepts_supported_commands(actuator, command, expected_state):
    assert actuator.execute(command) is True
    assert actuator.state.value == expected_state


@pytest.mark.parametrize(
    ("actuator", "command"),
    [
        (FanActuator("fan_1"), ActuatorState.OPEN),
        (HeaterActuator("heater_1"), ActuatorState.CLOSED),
        (LockActuator("lock_1"), ActuatorState.ON),
        (FanActuator("fan_1"), "invalid"),
    ],
)
def test_execute_rejects_unsupported_commands_without_mutating_state(actuator, command):
    initial_state = actuator.state

    assert actuator.execute(command) is False
    assert actuator.state is initial_state


def test_unknown_actuator_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        create_actuator("unknown", "actuator_1")

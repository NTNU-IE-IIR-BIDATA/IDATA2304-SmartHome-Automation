import operator
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


from ..common.constants import AnomalySeverity, SensorType, AnomalyThresholdLabels

@dataclass
class Anomaly:
    node_id: str
    sensor_id: str
    value: str | int | float | bool
    unit: str
    message: str
    severity: AnomalySeverity
    timestamp: datetime

class AnomalyDetector:

    NUMERICAL_THRESHOLDS = {
        SensorType.TEMPERATURE: {
            AnomalyThresholdLabels.WARNING_MIN: 10,
            AnomalyThresholdLabels.WARNING_MAX: 35,
            AnomalyThresholdLabels.CRITICAL_MIN: 5,
            AnomalyThresholdLabels.CRITICAL_MAX: 50
        },
        SensorType.HUMIDITY: {
            AnomalyThresholdLabels.WARNING_MIN: 20,
            AnomalyThresholdLabels.WARNING_MAX: 75,
            AnomalyThresholdLabels.CRITICAL_MIN: 10,
            AnomalyThresholdLabels.CRITICAL_MAX: 90
        },
        SensorType.POWER: {
            AnomalyThresholdLabels.WARNING_MIN: None,
            AnomalyThresholdLabels.WARNING_MAX: 4000.0,
            AnomalyThresholdLabels.CRITICAL_MIN: None,
            AnomalyThresholdLabels.CRITICAL_MAX: 10000.0
        },
        SensorType.AIR_QUALITY: {
            AnomalyThresholdLabels.WARNING_MIN: None,
            AnomalyThresholdLabels.WARNING_MAX: 150,
            AnomalyThresholdLabels.CRITICAL_MIN: None,
            AnomalyThresholdLabels.CRITICAL_MAX:200
        }
    }

    BOOLEAN_THRESHOLDS = {
        SensorType.SMOKE: {
            AnomalySeverity.CRITICAL: True
        },
        SensorType.LEAK: {
            AnomalySeverity.CRITICAL: True
        }
    }

    CHECKS = (
        (AnomalyThresholdLabels.CRITICAL_MAX, operator.gt, AnomalySeverity.CRITICAL, "is over threshold"),
        (AnomalyThresholdLabels.CRITICAL_MIN, operator.lt, AnomalySeverity.CRITICAL, "is under threshold"),
        (AnomalyThresholdLabels.WARNING_MAX, operator.gt, AnomalySeverity.WARNING, "is over threshold"),
        (AnomalyThresholdLabels.WARNING_MIN, operator.lt, AnomalySeverity.WARNING, "is under threshold")
    )

    def evaluate(
        self,
        node_id: str,
        sensor_id: str,
        sensor_type: SensorType,
        value: str | int | float | bool,
        unit: str,
    ) -> Optional[Anomaly]:
        """
        Evaluate sensor data against set thresholds. Returns an anomaly if the value exceeds the min/max
        :param sensor_type: type of the sensor
        :param node_id: id of the node
        :param sensor_id: id of the sensor
        :param value: value to check
        :param unit: measurement unit of the value
        :return: Anomaly if value exceeds threshold. None otherwise
        """

        if isinstance(value, bool): # boolean value
            violation = self._evaluate_boolean(value, sensor_type)
            if violation is not None:
                severity, description = violation
                return self._create_anomaly(
                    node_id=node_id,
                    sensor_id=sensor_id,
                    value=value,
                    unit=unit,
                    severity=severity,
                    message=f"Sensor alert from {node_id}.{sensor_id} ({sensor_type.value}): {description}",
                )
            return None

        if isinstance(value, (int, float)): # numerical value
            violation = self._evaluate_numerical(value, sensor_type)
            if violation is not None:
                severity, description, threshold = violation
                return self._create_anomaly(
                    node_id=node_id,
                    sensor_id=sensor_id,
                    value=value,
                    unit=unit,
                    severity=severity,
                    message=f"Sensor data from {node_id}.{sensor_id} {value} {unit} {description} {threshold}",
                )
            return None

        return None

    def _evaluate_numerical(
        self, value: int | float, sensor_type: SensorType
    ) -> Optional[tuple[AnomalySeverity, str, int | float]]:
        thresholds = self.NUMERICAL_THRESHOLDS.get(sensor_type)
        if thresholds is None:
            return None

        for label, op, severity, description in self.CHECKS:
            threshold = thresholds.get(label)
            if threshold is None:
                continue

            if op(value, threshold):
                return (severity, description, threshold)

        return None

    def _evaluate_boolean(
        self, value: bool, sensor_type: SensorType
    ) -> Optional[tuple[AnomalySeverity, str]]:
        rules = self.BOOLEAN_THRESHOLDS.get(sensor_type)
        if rules is None:
            return None

        for severity, trigger_value in rules.items():
            if value == trigger_value:
                return severity, f"detected alert state ({value})"

        return None

    def _create_anomaly(
        self,
        node_id: str,
        sensor_id: str,
        value: str | int | float | bool,
        unit: str,
        message: str,
        severity: AnomalySeverity,
    ) -> Anomaly:
        return Anomaly(
            node_id=node_id,
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
        )
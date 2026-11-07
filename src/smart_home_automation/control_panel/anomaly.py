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

    def evaluate(self, node_id: str, sensor_id: str, sensor_type: SensorType, value: str | int | float | bool, unit: str) -> Optional[Anomaly]:
        """
        Evaluate sensor data against set thresholds. Returns an anomaly if the value exceeds the min/max
        :param sensor_type: type of the sensor
        :param node_id: id of the node
        :param sensor_id: id of the sensor
        :param value: value to check
        :param unit: measurement unit of the value
        :return: Anomaly if value exceeds threshold. None otherwise
        """

        if type(value) == int | type(value) == float: # Numerical value
            if value > self.NUMERICAL_THRESHOLDS[sensor_type][AnomalyThresholdLabels.CRITICAL_MAX]:
                raise NotImplemented

            if value < self.NUMERICAL_THRESHOLDS[sensor_type][AnomalyThresholdLabels.CRITICAL_MIN]:
                raise NotImplemented

            if value > self.NUMERICAL_THRESHOLDS[sensor_type][AnomalyThresholdLabels.WARNING_MAX]:
                raise NotImplemented

            if value > self.NUMERICAL_THRESHOLDS[sensor_type][AnomalyThresholdLabels.WARNING_MIN]:
                raise NotImplemented

        if type(value) == bool: # boolean value
            raise NotImplemented

    def _create_anomaly(self,
                        node_id: str,
                        sensor_id: str,
                        value: str | int | float | bool,
                        unit: str,
                        message: str,
                        severity: AnomalySeverity
                        ) -> Anomaly:
        return Anomaly(
            node_id=node_id,
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            severity=severity,
            message=message,
            timestamp=datetime.now()
        )

    """
    have some value thresholds to check against
    evaluate against those thresholds
    if over critical, return critical anomaly
    if over warning, return warning anomaly
    else, return nothing
    
    how to check against boolean values?
    sensor type dict containing sensor type
    
    check first if sensor data is numerical or boolean. if it is none, we do nothing
    """
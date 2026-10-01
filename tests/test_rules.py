from datetime import datetime

from sedp.models import EquipmentEvent
from sedp.rules import (
    VacuumPressureRule,
    CoolingTemperatureRule,
    CoolingFaultSequenceRule,
)


def test_vacuum_pressure_rule_detects_fault():

    event = EquipmentEvent(
        timestamp=datetime(2026, 9, 26, 10, 0, 0),
        equipment_id="Sigma",
        subsystem="Vacuum",
        component="Chamber",
        event_code="VAC_PRESSURE",
        severity="warning",
        value=8.5e-3,
        unit="mbar",
    )

    rule = VacuumPressureRule()

    result = rule.evaluate(event)

    assert result is not None
    assert result.fault_code == "VAC-001"
    assert result.status.value == "fault"
    assert result.priority == 5


def test_cooling_temperature_rule_assigns_priority():

    event = EquipmentEvent(
        timestamp=datetime(2026, 9, 26, 12, 30, 30),
        equipment_id="SEDP-SEM-001",
        subsystem="cooling",
        component="temperature_sensor",
        event_code="COOLING_TEMP_HIGH",
        severity="ERROR",
        value=32.5,
        unit="°C",
    )

    rule = CoolingTemperatureRule()

    result = rule.evaluate(event)

    assert result is not None
    assert result.fault_code == "COOL-001"
    assert result.priority == 5
    assert result.confidence == 0.95


def test_cooling_fault_sequence_rule_assigns_higher_priority():

    events = [
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 10, 0, 0),
            equipment_id="SEDP-SEM-001",
            subsystem="cooling",
            component="cooling_pump",
            event_code="COOLING_PUMP_ON",
            severity="INFO",
            value=1,
            unit=None,
        ),
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 10, 0, 5),
            equipment_id="SEDP-SEM-001",
            subsystem="cooling",
            component="flow_sensor",
            event_code="COOLING_FLOW_LOW",
            severity="WARNING",
            value=0.82,
            unit="L/min",
        ),
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 10, 0, 10),
            equipment_id="SEDP-SEM-001",
            subsystem="cooling",
            component="temperature_sensor",
            event_code="COOLING_TEMP_HIGH",
            severity="ERROR",
            value=32.5,
            unit="°C",
        ),
    ]

    rule = CoolingFaultSequenceRule()

    result = rule.evaluate(events)

    assert result is not None
    assert result.fault_code == "COOL-002"
    assert result.priority == 10
    assert result.confidence == 0.98
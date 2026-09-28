from datetime import datetime

from sedp.models import EquipmentEvent
from sedp.rules import VacuumPressureRule


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
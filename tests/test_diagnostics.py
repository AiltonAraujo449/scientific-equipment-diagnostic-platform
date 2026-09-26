from datetime import datetime

from sedp.diagnostics import diagnose, DiagnosticStatus
from sedp.models import EquipmentEvent


def test_detect_high_vacuum_pressure():

    events = [
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 10, 0, 0),
            equipment_id="Sigma",
            subsystem="Vacuum",
            component="Chamber",
            event_code="VAC_PRESSURE",
            severity="warning",
            value=8.5e-3,
            unit="mbar",
        )
    ]

    result = diagnose(events)

    assert result.status == DiagnosticStatus.FAULT
    assert result.subsystem == "vacuum"
    assert result.fault_code == "VAC-001"
    assert result.confidence > 0.9
    assert len(result.evidence) > 0
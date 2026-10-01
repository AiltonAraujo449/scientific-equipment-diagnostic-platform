from datetime import datetime
from pathlib import Path

from sedp import evidence
from sedp.diagnostics import diagnose
from sedp.diagnostic_models import DiagnosticStatus
from sedp.models import EquipmentEvent
from sedp.ingestion import load_events_from_json

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

    evidence = result.evidence[0]

    assert evidence.event_code == "VAC_PRESSURE"
    assert evidence.value == 8.5e-3
    assert evidence.unit == "mbar"
    assert evidence.severity == "warning"


def test_detect_high_cooling_temperature():

    events = [
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 12, 30, 30),
            equipment_id="SEDP-SEM-001",
            subsystem="cooling",
            component="temperature_sensor",
            event_code="COOLING_TEMP_HIGH",
            severity="ERROR",
            value=32.5,
            unit="°C",
        )
    ]

    result = diagnose(events)

    assert result.status == DiagnosticStatus.FAULT
    assert result.subsystem == "cooling"
    assert result.fault_code == "COOL-001"
    assert result.confidence > 0.9
    assert len(result.evidence) > 0

    evidence = result.evidence[0]

    assert evidence.event_code == "COOLING_TEMP_HIGH"
    assert evidence.value == 32.5
    assert evidence.unit == "°C"
    assert evidence.severity == "ERROR"

def test_diagnose_cooling_fault_sequence_from_json():

    path = Path("examples/cooling-fault-sequence.json")

    events = load_events_from_json(path)

    result = diagnose(events)

    assert result.status == DiagnosticStatus.FAULT
    assert result.equipment == "SEDP-SEM-001"
    assert result.subsystem == "cooling"
    assert result.fault_code == "COOL-001"
    assert result.confidence > 0.9

    assert len(result.evidence) > 0
    assert result.evidence[0].event_code == "COOLING_TEMP_HIGH"

    assert len(result.recommended_actions) > 0

def test_diagnose_without_fault_returns_normal():

    events = [
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 14, 0, 0),
            equipment_id="SEDP-SEM-001",
            subsystem="cooling",
            component="temperature_sensor",
            event_code="COOLING_TEMP_HIGH",
            severity="INFO",
            value=25.0,
            unit="°C",
        )
    ]

    result = diagnose(events)

    assert result.status == DiagnosticStatus.NORMAL
    assert result.equipment == "SEDP-SEM-001"
    assert result.fault_code is None
    assert result.confidence == 0.90


def test_diagnose_sequence_collects_multiple_faults():

    events = [
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 10, 0, 0),
            equipment_id="SEDP-SEM-001",
            subsystem="Vacuum",
            component="Chamber",
            event_code="VAC_PRESSURE",
            severity="warning",
            value=8.5e-3,
            unit="mbar",
        ),
        EquipmentEvent(
            timestamp=datetime(2026, 9, 26, 10, 1, 0),
            equipment_id="SEDP-SEM-001",
            subsystem="cooling",
            component="temperature_sensor",
            event_code="COOLING_TEMP_HIGH",
            severity="ERROR",
            value=32.5,
            unit="°C",
        ),
    ]

    result = diagnose(events)

    assert result.status == DiagnosticStatus.FAULT
    assert result.equipment == "SEDP-SEM-001"
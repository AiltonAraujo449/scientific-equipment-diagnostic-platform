from datetime import datetime, timezone
from pathlib import Path

from sedp.models import EquipmentEvent


def test_equipment_event_creation():
    event = EquipmentEvent(
        timestamp=datetime.now(timezone.utc),
        equipment_id="SEDP-SEM-001",
        subsystem="cooling",
        component="flow_sensor",
        event_code="COOLING_FLOW_LOW",
        severity="WARNING",
        value=0.82,
        unit="L/min",
    )

    assert event.equipment_id == "SEDP-SEM-001"
    assert event.event_code == "COOLING_FLOW_LOW"
    assert event.value == 0.82

    
from sedp.ingestion import load_event_from_json, load_events_from_json


def test_load_equipment_event_from_json():
    path = Path("examples/equipment-event.json")

    event = load_event_from_json(path)

    assert event.equipment_id == "SEDP-SEM-001"
    assert event.subsystem == "cooling"
    assert event.component == "flow_sensor"
    assert event.event_code == "COOLING_FLOW_LOW"
    assert event.severity == "WARNING"
    assert event.value == 0.82
    assert event.unit == "L/min"
    assert event.timestamp.isoformat() == "2026-09-26T12:30:15+00:00"

    from sedp.ingestion import load_events_from_json


def test_load_event_sequence_from_json():
    path = Path("examples/cooling-fault-sequence.json")

    events = load_events_from_json(path)

    assert len(events) == 3

    assert events[0].event_code == "COOLING_PUMP_ON"
    assert events[1].event_code == "COOLING_FLOW_LOW"
    assert events[2].event_code == "COOLING_TEMP_HIGH"

    assert events[1].value == 0.82
    assert events[2].value == 32.5
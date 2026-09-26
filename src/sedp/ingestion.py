import json
from datetime import datetime
from pathlib import Path

from sedp.models import EquipmentEvent


def equipment_event_from_dict(data: dict) -> EquipmentEvent:
    timestamp = datetime.fromisoformat(
        data["timestamp"].replace("Z", "+00:00")
    )

    return EquipmentEvent(
        timestamp=timestamp,
        equipment_id=data["equipment_id"],
        subsystem=data["subsystem"],
        component=data["component"],
        event_code=data["event_code"],
        severity=data["severity"],
        value=float(data["value"]) if data.get("value") is not None else None,
        unit=data.get("unit"),
    )


def load_event_from_json(path: str | Path) -> EquipmentEvent:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return equipment_event_from_dict(data)


def load_events_from_json(path: str | Path) -> list[EquipmentEvent]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return [equipment_event_from_dict(item) for item in data]
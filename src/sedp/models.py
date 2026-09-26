from dataclasses import dataclass
from datetime import datetime


@dataclass
class EquipmentEvent:
    timestamp: datetime
    equipment_id: str
    subsystem: str
    component: str
    event_code: str
    severity: str
    value: float | None = None
    unit: str | None = None
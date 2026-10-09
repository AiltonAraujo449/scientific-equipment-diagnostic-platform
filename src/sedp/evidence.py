from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiagnosticEvidence:

    event_code: str
    description: str
    value: float | None = None
    unit: str | None = None
    severity: str | None = None
    timestamp: datetime | None = None
    elapsed_seconds: float | None = None


@dataclass
class DiagnosticSequenceEvidence:

    events: list[DiagnosticEvidence]
    total_duration_seconds: float
from dataclasses import dataclass


@dataclass
class DiagnosticEvidence:
    event_code: str
    description: str
    value: float | None = None
    unit: str | None = None
    severity: str | None = None
    
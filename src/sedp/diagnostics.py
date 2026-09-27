from dataclasses import dataclass, field
from enum import Enum
from .models import EquipmentEvent
from .evidence import DiagnosticEvidence

class DiagnosticStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    FAULT = "fault"
    UNKNOWN = "unknown"


@dataclass
class DiagnosticResult:
    status: DiagnosticStatus
    equipment: str
    subsystem: str
    fault_code: str | None = None
    title: str | None = None
    description: str | None = None
    confidence: float = 0.0
    evidence: list[DiagnosticEvidence] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


    
def diagnose(events: list[EquipmentEvent]) -> DiagnosticResult:
    vacuum_events = [
        event
        for event in events
        if event.subsystem.lower() == "vacuum"
    ]

    if not vacuum_events:
        return DiagnosticResult(
            status=DiagnosticStatus.UNKNOWN,
            equipment="unknown",
            subsystem="vacuum",
            title="Insufficient data",
            description="No vacuum events were found.",
        )

    equipment = vacuum_events[0].equipment_id

    for event in vacuum_events:
        if (
            event.value is not None
            and event.unit == "mbar"
            and event.value > 1e-3
        ):
            return DiagnosticResult(
                status=DiagnosticStatus.FAULT,
                equipment=equipment,
                subsystem="vacuum",
                fault_code="VAC-001",
                title="Vacuum pressure above expected level",
                description=(
                    "The vacuum pressure is above the expected "
                    "operating range."
                ),
                confidence=0.95,
                evidence=[
                    DiagnosticEvidence(
                        event_code=event.event_code,
                        description=f"Vacuum pressure measured at {event.value} {event.unit}",
                        value=event.value,
                        unit=event.unit,
                        severity=event.severity,
                    )           
                ],
                recommended_actions=[
                    "Check the vacuum system for possible leakage.",
                    "Verify pump operation.",
                    "Inspect relevant vacuum components.",
                ],
            )

    return DiagnosticResult(
        status=DiagnosticStatus.NORMAL,
        equipment=equipment,
        subsystem="vacuum",
        title="Vacuum system operating normally",
        description="No abnormal vacuum condition was detected.",
        confidence=0.90,
    )
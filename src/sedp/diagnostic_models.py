from dataclasses import dataclass, field
from enum import Enum

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
    priority: int = 0    
    evidence: list[DiagnosticEvidence] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
from abc import ABC, abstractmethod

from .diagnostic_models import DiagnosticResult, DiagnosticStatus
from .models import EquipmentEvent
from .evidence import DiagnosticEvidence


class DiagnosticRule(ABC):
    @abstractmethod
    def applies(self, event: EquipmentEvent) -> bool:
        """Return True when this rule can evaluate the event."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, event: EquipmentEvent) -> DiagnosticResult | None:
        """Evaluate the event and return a diagnosis when a fault is detected."""
        raise NotImplementedError


class VacuumPressureRule(DiagnosticRule):

    FAULT_CODE = "VAC-001"
    PRESSURE_LIMIT = 1e-3

    def applies(self, event: EquipmentEvent) -> bool:
        return (
            event.subsystem.lower() == "vacuum"
            and event.event_code == "VAC_PRESSURE"
            and event.value is not None
            and event.unit == "mbar"
        )

    def evaluate(self, event: EquipmentEvent) -> DiagnosticResult | None:
        if not self.applies(event):
            return None

        if event.value <= self.PRESSURE_LIMIT:
            return None

        evidence = DiagnosticEvidence(
            event_code=event.event_code,
            description=(
                f"Vacuum pressure measured at "
                f"{event.value} {event.unit}"
            ),
            value=event.value,
            unit=event.unit,
            severity=event.severity,
        )

        return DiagnosticResult(
            status=DiagnosticStatus.FAULT,
            equipment=event.equipment_id,
            subsystem="vacuum",
            fault_code=self.FAULT_CODE,
            title="Vacuum pressure above expected level",
            description=(
                "The vacuum pressure is above the expected "
                "operating range."
            ),
            confidence=0.95,
            evidence=[evidence],
            recommended_actions=[
                "Check the vacuum system for possible leakage.",
                "Verify pump operation.",
                "Inspect relevant vacuum components.",
            ],
        )
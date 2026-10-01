from .models import EquipmentEvent
from .diagnostic_models import DiagnosticResult, DiagnosticStatus
from .rules import (
    DiagnosticRule,
    VacuumPressureRule,
    CoolingTemperatureRule,
)


class DiagnosticEngine:
    """Engine responsible for evaluating equipment events."""

    def __init__(self, rules: list[DiagnosticRule] | None = None):
        self.rules = rules if rules is not None else [
            VacuumPressureRule(),
            CoolingTemperatureRule(),
        ]

    def diagnose(self, events: list[EquipmentEvent]) -> DiagnosticResult:
        if not events:
            return DiagnosticResult(
                status=DiagnosticStatus.UNKNOWN,
                equipment="unknown",
                subsystem="unknown",
                title="Insufficient data",
                description="No equipment events were provided.",
            )

        for event in events:
            for rule in self.rules:
                if not rule.applies(event):
                    continue

                result = rule.evaluate(event)

                if result is not None:
                    return result

        equipment = events[0].equipment_id

        return DiagnosticResult(
            status=DiagnosticStatus.NORMAL,
            equipment=equipment,
            subsystem="unknown",
            title="No fault detected",
            description="No diagnostic rule detected an abnormal condition.",
            confidence=0.90,
        )


def diagnose(events: list[EquipmentEvent]) -> DiagnosticResult:
    """Diagnose a sequence of equipment events."""

    engine = DiagnosticEngine()
    return engine.diagnose(events)
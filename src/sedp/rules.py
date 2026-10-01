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

class DiagnosticSequenceRule(ABC):

    @abstractmethod
    def applies(self, events: list[EquipmentEvent]) -> bool:
        """Return True when this rule can evaluate the event sequence."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        events: list[EquipmentEvent],
    ) -> DiagnosticResult | None:
        """Evaluate the event sequence."""
        raise NotImplementedError
    
class VacuumPressureRule(DiagnosticRule):

    FAULT_CODE = "VAC-001"
    PRESSURE_LIMIT = 1e-3
    PRIORITY = 5

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
            priority=self.PRIORITY,
            evidence=[evidence],
            recommended_actions=[
                "Check the vacuum system for possible leakage.",
                "Verify pump operation.",
                "Inspect relevant vacuum components.",
            ],
        )


class CoolingTemperatureRule(DiagnosticRule):

    FAULT_CODE = "COOL-001"
    TEMPERATURE_LIMIT = 30.0
    PRIORITY = 5

    def applies(self, event: EquipmentEvent) -> bool:
        return (
            event.subsystem.lower() == "cooling"
            and event.event_code == "COOLING_TEMP_HIGH"
            and event.value is not None
        )

    def evaluate(self, event: EquipmentEvent) -> DiagnosticResult | None:
        if not self.applies(event):
            return None

        if event.value <= self.TEMPERATURE_LIMIT:
            return None

        evidence = DiagnosticEvidence(
            event_code=event.event_code,
            description=(
                f"Cooling temperature measured at "
                f"{event.value} {event.unit}"
            ),
            value=event.value,
            unit=event.unit,
            severity=event.severity,
        )

        return DiagnosticResult(
            status=DiagnosticStatus.FAULT,
            equipment=event.equipment_id,
            subsystem="cooling",
            fault_code=self.FAULT_CODE,
            title="Cooling temperature above expected level",
            description=(
                "The cooling temperature is above the expected "
                "operating range."
            ),
            confidence=0.95,
            priority=self.PRIORITY,
            evidence=[evidence],
            recommended_actions=[
                "Check the cooling system.",
                "Verify cooling pump operation.",
                "Inspect coolant flow.",
                "Check the cooling temperature sensor.",
            ],
        )

class CoolingFaultSequenceRule(DiagnosticSequenceRule):

    FAULT_CODE = "COOL-002"
    PRIORITY = 10

    REQUIRED_EVENTS = {
        "COOLING_PUMP_ON",
        "COOLING_FLOW_LOW",
        "COOLING_TEMP_HIGH",
    }

    def applies(self, events: list[EquipmentEvent]) -> bool:
        if not events:
            return False

        event_codes = {
            event.event_code
            for event in events
            if event.subsystem.lower() == "cooling"
        }

        return self.REQUIRED_EVENTS.issubset(event_codes)

    def evaluate(
        self,
        events: list[EquipmentEvent],
    ) -> DiagnosticResult | None:

        if not self.applies(events):
            return None

        cooling_events = [
            event
            for event in events
            if event.subsystem.lower() == "cooling"
            and event.event_code in self.REQUIRED_EVENTS
        ]

        cooling_events.sort(key=lambda event: event.timestamp)

        evidence = []

        for event in cooling_events:
            evidence.append(
                DiagnosticEvidence(
                    event_code=event.event_code,
                    description=(
                        f"{event.event_code} detected"
                        + (
                            f" at {event.value} {event.unit}"
                            if event.value is not None
                            and event.unit is not None
                            else ""
                        )
                    ),
                    value=event.value,
                    unit=event.unit,
                    severity=event.severity,
                )
            )

        return DiagnosticResult(
            status=DiagnosticStatus.FAULT,
            equipment=cooling_events[0].equipment_id,
            subsystem="cooling",
            fault_code=self.FAULT_CODE,
            title="Cooling system degradation detected",
            description=(
                "The event sequence indicates a possible cooling "
                "system degradation: the cooling pump was active, "
                "coolant flow was low, and cooling temperature "
                "increased above the expected operating range."
            ),
            confidence=0.98,
            priority=self.PRIORITY,
            evidence=evidence,
            recommended_actions=[
                "Check cooling pump operation.",
                "Inspect coolant flow and possible restrictions.",
                "Verify coolant level and cooling circuit condition.",
                "Check the cooling temperature sensor.",
            ],
        )
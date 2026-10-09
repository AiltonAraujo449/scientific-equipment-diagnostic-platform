from abc import ABC, abstractmethod
from datetime import timedelta

from .diagnostic_models import DiagnosticResult, DiagnosticStatus
from .models import EquipmentEvent
from .evidence import (
    DiagnosticEvidence,
    DiagnosticSequenceEvidence,
)

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
    MAX_INTERVAL_SECONDS = 60

    REQUIRED_EVENTS = {
        "COOLING_PUMP_ON",
        "COOLING_FLOW_LOW",
        "COOLING_TEMP_HIGH",
    }

    def applies(self, events: list[EquipmentEvent]) -> bool:
        if not events:
            return False

        cooling_events = sorted(
            [
                event
                for event in events
                if event.subsystem.lower() == "cooling"
                and event.event_code in self.REQUIRED_EVENTS
            ],
            key=lambda event: event.timestamp,
        )

        max_interval = timedelta(seconds=self.MAX_INTERVAL_SECONDS)

        pump_events = [
            event
            for event in cooling_events
            if event.event_code == "COOLING_PUMP_ON"
        ]

        flow_events = [
            event
            for event in cooling_events
            if event.event_code == "COOLING_FLOW_LOW"
        ]

        temperature_events = [
            event
            for event in cooling_events
            if event.event_code == "COOLING_TEMP_HIGH"
        ]

        for pump in pump_events:
            for flow in flow_events:
                if flow.timestamp <= pump.timestamp:
                    continue

                if flow.timestamp - pump.timestamp > max_interval:
                    break

                for temperature in temperature_events:
                    if temperature.timestamp <= flow.timestamp:
                        continue

                    if temperature.timestamp - flow.timestamp > max_interval:
                        break

                    return True

        return False

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

        # Find the actual temporal chain that triggered the rule.
        pump_event = next(
            event
            for event in cooling_events
            if event.event_code == "COOLING_PUMP_ON"
        )

        flow_event = next(
            event
            for event in cooling_events
            if (
                event.event_code == "COOLING_FLOW_LOW"
                and event.timestamp > pump_event.timestamp
                and (
                    event.timestamp - pump_event.timestamp
                ).total_seconds()
                <= self.MAX_INTERVAL_SECONDS
            )
        )

        temperature_event = next(
            event
            for event in cooling_events
            if (
                event.event_code == "COOLING_TEMP_HIGH"
                and event.timestamp > flow_event.timestamp
                and (
                    event.timestamp - flow_event.timestamp
                ).total_seconds()
                <= self.MAX_INTERVAL_SECONDS
            )
        )

        pump_to_flow = (
            flow_event.timestamp - pump_event.timestamp
        ).total_seconds()

        flow_to_temperature = (
            temperature_event.timestamp - flow_event.timestamp
        ).total_seconds()

        evidence = [
            DiagnosticEvidence(
                event_code=pump_event.event_code,
                description="Cooling pump activated.",
                value=pump_event.value,
                unit=pump_event.unit,
                severity=pump_event.severity,
                timestamp=pump_event.timestamp,
                elapsed_seconds=None,
            ),
            DiagnosticEvidence(
                event_code=flow_event.event_code,
                description=(
                    "Cooling flow became low after pump activation."
                ),
                value=flow_event.value,
                unit=flow_event.unit,
                severity=flow_event.severity,
                timestamp=flow_event.timestamp,
                elapsed_seconds=pump_to_flow,
            ),
            DiagnosticEvidence(
                event_code=temperature_event.event_code,
                description=(
                    "Cooling temperature became high "
                    "after low cooling flow."
                ),
                value=temperature_event.value,
                unit=temperature_event.unit,
                severity=temperature_event.severity,
                timestamp=temperature_event.timestamp,
                elapsed_seconds=flow_to_temperature,
            ),
        ]

        sequence_evidence = DiagnosticSequenceEvidence(
            events=evidence,
            total_duration_seconds=(
                temperature_event.timestamp - pump_event.timestamp
            ).total_seconds(),
        )

        return DiagnosticResult(
            status=DiagnosticStatus.FAULT,
            equipment=pump_event.equipment_id,
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
            sequence_evidence=sequence_evidence,
            recommended_actions=[
                "Check cooling pump operation.",
                "Inspect coolant flow and possible restrictions.",
                "Verify coolant level and cooling circuit condition.",
                "Check the cooling temperature sensor.",
    ],
)
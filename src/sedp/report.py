from dataclasses import dataclass

from .diagnostic_models import DiagnosticResult, DiagnosticStatus
from .evidence import DiagnosticEvidence

import json

@dataclass
class DiagnosticReport:
    equipment: str
    status: DiagnosticStatus
    fault_code: str | None
    title: str
    priority: int
    confidence: float
    explanation: str
    evidence: list[DiagnosticEvidence]
    recommended_actions: list[str]

    @classmethod
    def from_result(
        cls,
        result: DiagnosticResult,
        explanation: str,
    ) -> "DiagnosticReport":
        return cls(
            equipment=result.equipment,
            status=result.status,
            fault_code=result.fault_code,
            title=result.title,
            priority=result.priority,
            confidence=result.confidence,
            explanation=explanation,
            evidence=result.evidence,
            recommended_actions=result.recommended_actions,
        )

    def to_text(self) -> str:
        lines = [
            "DIAGNOSTIC REPORT",
            "────────────────────────────────",
            "",
            f"Equipment: {self.equipment}",
            "",
            f"Status: {self.status.value.upper()}",
            "",
            f"Fault code: {self.fault_code or 'N/A'}",
            "",
            f"Title: {self.title}",
            "",
            f"Priority: {self.priority}",
            "",
            f"Confidence: {self.confidence:.0%}",
            "",
            "Explanation:",
            self.explanation,
            "",
            "Evidence:",
        ]

        for index, evidence in enumerate(self.evidence, start=1):
            elapsed = ""

            if evidence.elapsed_seconds is not None:
                elapsed = f" (+{evidence.elapsed_seconds:g} s)"

            lines.append(
                f"{index}. {evidence.event_code}{elapsed}"
            )

        lines.extend(
            [
                "",
                "Recommended actions:",
            ]
        )

        for action in self.recommended_actions:
            lines.append(f"- {action}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "equipment": self.equipment,
            "status": self.status.value.upper(),
            "fault_code": self.fault_code,
            "title": self.title,
            "priority": self.priority,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence": [
                {
                    "event_code": evidence.event_code,
                    "description": evidence.description,
                    "value": evidence.value,
                    "unit": evidence.unit,
                    "severity": evidence.severity,
                    "timestamp": (
                        evidence.timestamp.isoformat()
                        if evidence.timestamp is not None
                        else None
                    ),
                    "elapsed_seconds": evidence.elapsed_seconds,
                }
                for evidence in self.evidence
            ],
            "recommended_actions": self.recommended_actions,
        }
    
    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            indent=2,
            ensure_ascii=False,
        )
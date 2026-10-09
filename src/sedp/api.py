
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

from .diagnostics import DiagnosticEngine
from .models import EquipmentEvent
from .report import DiagnosticReport


app = FastAPI(
    title="Scientific Equipment Diagnostic Platform",
    description="API for scientific equipment diagnostics.",
    version="0.1.0",
)

engine = DiagnosticEngine()


class DiagnosticRequest(BaseModel):
    events: list[dict] = Field(
        ...,
        description="List of equipment events to analyze.",
    )


def parse_event(data: dict) -> EquipmentEvent:
    event_data = data.copy()

    timestamp = event_data.get("timestamp")
    if isinstance(timestamp, str):
        event_data["timestamp"] = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

    value = event_data.get("value")
    if value is not None:
        event_data["value"] = float(value)

    return EquipmentEvent(**event_data)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/diagnostics")
def diagnose_equipment(request: DiagnosticRequest) -> dict:
    try:
        events = [parse_event(event) for event in request.events]
        result = engine.diagnose(events)

        report = DiagnosticReport.from_result(
            result,
            explanation=result.description,
        )

        return report.to_dict()

    except (ValueError, TypeError, ValidationError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid diagnostic input: {exc}",
        ) from exc
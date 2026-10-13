from datetime import datetime

from fastapi import FastAPI, HTTPException, Path as PathParam, Query
from psycopg import Error as PsycopgError
from pydantic import BaseModel, Field, ValidationError

from .diagnostics import DiagnosticEngine
from .models import EquipmentEvent
from .report import DiagnosticReport

from .repository import (
    get_connection,
    get_report,
    is_database_enabled,
    list_reports,
    save_report,
)


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

@app.get("/ready")
def readiness_check() -> dict[str, str]:
    if not is_database_enabled():
        return {
            "status": "ready",
            "database": "disabled",
        }

    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")

    except (PsycopgError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Service is not ready.",
        ) from exc

    return {
        "status": "ready",
        "database": "ok",
    }

@app.post("/diagnostics")
def diagnose_equipment(request: DiagnosticRequest) -> dict:
    try:
        events = [parse_event(event) for event in request.events]
        result = engine.diagnose(events)
        report = DiagnosticReport.from_result(
            result,
            explanation=result.description,
        )
    except (ValueError, TypeError, ValidationError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid diagnostic input: {exc}",
        ) from exc

    if is_database_enabled():
        try:
            save_report(report)
        except (PsycopgError, RuntimeError) as exc:
            raise HTTPException(
                status_code=503,
                detail="Diagnostic report persistence is unavailable.",
            ) from exc

    return report.to_dict()


@app.get("/diagnostics/history")
def diagnostic_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    equipment: str | None = None,
    fault_code: str | None = None,
) -> dict:
    if not is_database_enabled():
        raise HTTPException(
            status_code=503,
            detail="Diagnostic history is disabled.",
        )

    try:
        reports = list_reports(
            limit=limit,
            offset=offset,
            equipment=equipment,
            fault_code=fault_code,
        )

        return {
            "items": reports,
            "limit": limit,
            "offset": offset,
            "count": len(reports),
        }

    except (PsycopgError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Diagnostic history database is unavailable.",
        ) from exc


@app.get("/diagnostics/history/{report_id}")
def diagnostic_history_by_id(
    report_id: int = PathParam(gt=0),
) -> dict:
    if not is_database_enabled():
        raise HTTPException(
            status_code=503,
            detail="Diagnostic history is disabled.",
        )

    try:
        report = get_report(report_id)

    except (PsycopgError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Diagnostic history database is unavailable.",
        ) from exc

    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"Diagnostic report {report_id} was not found.",
        )

    return report

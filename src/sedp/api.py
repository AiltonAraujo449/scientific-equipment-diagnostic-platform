import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Path as PathParam, Query, Request
from psycopg import Error as PsycopgError
from pydantic import BaseModel, Field, ValidationError

from .diagnostics import DiagnosticEngine
from .models import EquipmentEvent
from .observability import (
    configure_logging,
    metrics_app,
    request_id_var,
)
from .report import DiagnosticReport
from .repository import (
    get_connection,
    get_report,
    is_database_enabled,
    list_reports,
    save_report,
)

from .observability import (
    DIAGNOSTICS_TOTAL,
    DIAGNOSTIC_DURATION,
    EVENTS_INGESTED,
    REQUEST_DURATION,
    configure_logging,
    metrics_app,
    request_id_var,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title="Scientific Equipment Diagnostic Platform",
    description="API for scientific equipment diagnostics.",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/metrics", metrics_app)

engine = DiagnosticEngine()



@app.middleware("http")
async def correlation_id_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(request_id)

    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response

    finally:
        elapsed = time.perf_counter() - start

        route = request.scope.get("route")
        endpoint = (
            getattr(route, "path", request.url.path)
            if route is not None
            else request.url.path
        )

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code),
        ).observe(elapsed)

        request_id_var.reset(token)


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
    start = time.perf_counter()

    try:
        try:
            events = [
                parse_event(event)
                for event in request.events
            ]

            result = engine.diagnose(events)

            report = DiagnosticReport.from_result(
                result,
                explanation=result.description,
            )

        except (
            ValueError,
            TypeError,
            ValidationError,
            KeyError,
        ) as exc:
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

        EVENTS_INGESTED.inc(len(events))

        DIAGNOSTICS_TOTAL.labels(
            outcome=str(result.status.value),
            severity=str(result.status.value),
        ).inc()

        logging.getLogger(__name__).info(
            "Diagnostic completed: equipment=%s fault_code=%s",
            report.equipment,
            report.fault_code,
        )

        return report.to_dict()

    finally:
        DIAGNOSTIC_DURATION.observe(
            time.perf_counter() - start
        )



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

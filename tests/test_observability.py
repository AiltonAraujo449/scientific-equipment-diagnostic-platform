
from fastapi.testclient import TestClient

from sedp.api import app
from sedp.observability import (
    DIAGNOSTICS_TOTAL,
    DIAGNOSTIC_DURATION,
    EVENTS_INGESTED,
)


client = TestClient(app)


def test_diagnostics_metrics_increment(monkeypatch):
    monkeypatch.setattr(
        "sedp.api.is_database_enabled",
        lambda: False,
    )

    events = [
        {
            "timestamp": "2026-09-26T12:30:00Z",
            "equipment_id": "SEDP-SEM-001",
            "subsystem": "cooling",
            "component": "cooling_pump",
            "event_code": "COOLING_PUMP_ON",
            "severity": "INFO",
            "value": 1,
            "unit": None,
        },
        {
            "timestamp": "2026-09-26T12:30:15Z",
            "equipment_id": "SEDP-SEM-001",
            "subsystem": "cooling",
            "component": "flow_sensor",
            "event_code": "COOLING_FLOW_LOW",
            "severity": "WARNING",
            "value": 0.82,
            "unit": "L/min",
        },
        {
            "timestamp": "2026-09-26T12:30:30Z",
            "equipment_id": "SEDP-SEM-001",
            "subsystem": "cooling",
            "component": "temperature_sensor",
            "event_code": "COOLING_TEMP_HIGH",
            "severity": "ERROR",
            "value": 32.5,
            "unit": "°C",
        },
    ]

    before_diagnostics = DIAGNOSTICS_TOTAL.labels(
        outcome="fault",
        severity="fault",
    )._value.get()

    before_events = EVENTS_INGESTED._value.get()

    before_duration = (
        DIAGNOSTIC_DURATION._sum.get()
    )

    response = client.post(
        "/diagnostics",
        json={"events": events},
    )

    assert response.status_code == 200
    assert response.json()["fault_code"] == "COOL-002"

    after_diagnostics = DIAGNOSTICS_TOTAL.labels(
        outcome="fault",
        severity="fault",
    )._value.get()

    after_events = EVENTS_INGESTED._value.get()

    after_duration = DIAGNOSTIC_DURATION._sum.get()

    assert after_diagnostics == before_diagnostics + 1
    assert after_events == before_events + 3
    assert after_duration >= before_duration


def test_metrics_endpoint_is_available():
    response = client.get("/metrics/")

    assert response.status_code == 200
    assert "sedp_events_ingested_total" in response.text
    assert "sedp_diagnostic_duration_seconds" in response.text

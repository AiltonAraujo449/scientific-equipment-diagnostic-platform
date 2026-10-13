
import json
from pathlib import Path

from fastapi.testclient import TestClient

from sedp.api import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnostics_with_empty_events():
    response = client.post(
        "/diagnostics",
        json={"events": []},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "UNKNOWN"
    assert data["title"] == "Insufficient data"
    assert data["evidence"] == []


def test_diagnostics_api_cooling_fault_sequence():
    example_path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "cooling-fault-sequence.json"
    )

    events = json.loads(
        example_path.read_text(encoding="utf-8")
    )

    response = client.post(
        "/diagnostics",
        json={"events": events},
    )

    assert response.status_code == 200

    data = response.json()

    # Resultado do diagnóstico
    assert data["status"] == "FAULT"
    assert data["fault_code"] == "COOL-002"
    assert data["priority"] == 10
    assert data["confidence"] == 0.98

    # Evidências cronológicas
    evidence = data["evidence"]

    assert len(evidence) == 3

    assert [
        item["event_code"] for item in evidence
    ] == [
        "COOLING_PUMP_ON",
        "COOLING_FLOW_LOW",
        "COOLING_TEMP_HIGH",
    ]

    # Intervalos temporais
    assert evidence[1]["elapsed_seconds"] == 15
    assert evidence[2]["elapsed_seconds"] == 15

    # Ações recomendadas
    actions = data["recommended_actions"]

    assert len(actions) > 0
    assert all(
        isinstance(action, str) and action.strip()
        for action in actions
    )


def test_diagnostics_with_invalid_event_returns_422():
    response = client.post(
        "/diagnostics",
        json={
            "events": [
                {
                    "timestamp": "not-a-valid-timestamp",
                    "equipment_id": "SEDP-TEST-001",
                    "subsystem": "cooling",
                    "component": "pump",
                    "event_code": "COOLING_PUMP_ON",
                    "severity": "INFO",
                }
            ]
        },
    )

    assert response.status_code == 422
    assert "Invalid diagnostic input" in response.json()["detail"]


def test_history_returns_503_when_database_is_disabled(monkeypatch):
    monkeypatch.setattr(
        "sedp.api.is_database_enabled",
        lambda: False,
    )

    response = client.get("/diagnostics/history")

    assert response.status_code == 503
    assert response.json()["detail"] == "Diagnostic history is disabled."


def test_history_by_id_returns_503_when_database_is_disabled(monkeypatch):
    monkeypatch.setattr(
        "sedp.api.is_database_enabled",
        lambda: False,
    )

    response = client.get("/diagnostics/history/1")

    assert response.status_code == 503
    assert response.json()["detail"] == "Diagnostic history is disabled."


def test_diagnostics_returns_503_when_persistence_fails(monkeypatch):
    from sedp import api

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: True,
    )

    def fail_save_report(report):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        api,
        "save_report",
        fail_save_report,
    )

    response = client.post(
        "/diagnostics",
        json={"events": []},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Diagnostic report persistence is unavailable."
    )


def test_diagnostics_returns_503_when_postgres_fails(monkeypatch):
    import psycopg
    from sedp import api

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: True,
    )

    def fail_save_report(report):
        raise psycopg.OperationalError(
            "Simulated PostgreSQL connection failure"
        )

    monkeypatch.setattr(
        api,
        "save_report",
        fail_save_report,
    )

    response = client.post(
        "/diagnostics",
        json={"events": []},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Diagnostic report persistence is unavailable."
    )


def test_history_returns_503_when_database_query_fails(monkeypatch):
    import psycopg
    from sedp import api

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: True,
    )

    def fail_list_reports(**kwargs):
        raise psycopg.OperationalError(
            "Simulated history query failure"
        )

    monkeypatch.setattr(api, "list_reports", fail_list_reports)

    response = client.get("/diagnostics/history")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Diagnostic history database is unavailable."
    )


def test_history_by_id_returns_503_when_database_query_fails(monkeypatch):
    import psycopg
    from sedp import api

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: True,
    )

    def fail_get_report(report_id):
        raise psycopg.OperationalError(
            "Simulated report retrieval failure"
        )

    monkeypatch.setattr(api, "get_report", fail_get_report)

    response = client.get("/diagnostics/history/1")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Diagnostic history database is unavailable."
    )


def test_readiness_returns_ready_when_database_is_disabled(monkeypatch):
    from sedp import api

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: False,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "disabled",
    }


def test_readiness_returns_ready_when_database_is_available(monkeypatch):
    from sedp import api

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, query):
            assert query == "SELECT 1"

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        api,
        "get_connection",
        lambda: FakeConnection(),
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
    }


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch):
    import psycopg
    from sedp import api

    monkeypatch.setattr(
        api,
        "is_database_enabled",
        lambda: True,
    )

    def fail_connection():
        raise psycopg.OperationalError(
            "Simulated database connection failure"
        )

    monkeypatch.setattr(
        api,
        "get_connection",
        fail_connection,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Service is not ready."



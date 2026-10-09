
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




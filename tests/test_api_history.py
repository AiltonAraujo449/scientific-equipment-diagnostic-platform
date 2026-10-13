import json
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sedp.api import app
from sedp.repository import (
    get_connection,
    initialize_database,
    is_database_enabled,
)


pytestmark = pytest.mark.skipif(
    os.getenv("SEDP_RUN_DB_TESTS") != "1",
    reason="Set SEDP_RUN_DB_TESTS=1 to run API database integration tests.",
)


@pytest.fixture(scope="module", autouse=True)
def database():
    if not is_database_enabled():
        pytest.skip("PostgreSQL persistence is disabled.")

    initialize_database()


@pytest.fixture
def created_equipment_ids():
    return set()


@pytest.fixture(autouse=True)
def cleanup_test_reports(created_equipment_ids):
    yield

    if not created_equipment_ids:
        return

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM diagnostic_reports
            WHERE equipment = ANY(%s)
            """,
            (list(created_equipment_ids),),
        )


client = TestClient(app)


def create_diagnostic(
    equipment_id: str,
    created_equipment_ids: set[str],
) -> dict:
    # Register the equipment so its test records can be cleaned up.
    created_equipment_ids.add(equipment_id)

    example_path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "cooling-fault-sequence.json"
    )

    events = json.loads(example_path.read_text(encoding="utf-8"))

    for event in events:
        event["equipment_id"] = equipment_id

    response = client.post("/diagnostics", json={"events": events})

    assert response.status_code == 200
    assert response.json()["fault_code"] == "COOL-002"

    history_response = client.get(
        "/diagnostics/history",
        params={"equipment": equipment_id},
    )

    assert history_response.status_code == 200

    items = history_response.json()["items"]
    matching = [
        item
        for item in items
        if item["report"]["equipment"] == equipment_id
    ]

    assert matching, "The diagnostic report was not persisted."
    return matching[0]


def test_api_persists_and_retrieves_report_by_id(
    created_equipment_ids,
):
    equipment_id = f"SEDP-API-{uuid.uuid4().hex[:8]}"

    stored = create_diagnostic(equipment_id, created_equipment_ids)

    response = client.get(
        f"/diagnostics/history/{stored['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == stored["id"]
    assert data["report"]["equipment"] == equipment_id
    assert data["report"]["fault_code"] == "COOL-002"


def test_api_history_filters_by_fault_code(
    created_equipment_ids,
):
    equipment_id = f"SEDP-API-{uuid.uuid4().hex[:8]}"

    stored = create_diagnostic(equipment_id, created_equipment_ids)

    response = client.get(
        "/diagnostics/history",
        params={
            "equipment": equipment_id,
            "fault_code": "COOL-002",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] >= 1
    assert any(
        item["id"] == stored["id"]
        for item in data["items"]
    )
    assert all(
        item["report"]["fault_code"] == "COOL-002"
        for item in data["items"]
    )


def test_api_history_supports_pagination(
    created_equipment_ids,
):
    equipment_id = f"SEDP-API-{uuid.uuid4().hex[:8]}"

    first = create_diagnostic(equipment_id, created_equipment_ids)
    second = create_diagnostic(equipment_id, created_equipment_ids)

    first_response = client.get(
        "/diagnostics/history",
        params={"equipment": equipment_id, "limit": 1, "offset": 0},
    )
    second_response = client.get(
        "/diagnostics/history",
        params={"equipment": equipment_id, "limit": 1, "offset": 1},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_page = first_response.json()["items"]
    second_page = second_response.json()["items"]

    assert len(first_page) == 1
    assert len(second_page) == 1
    assert first_page[0]["id"] == second["id"]
    assert second_page[0]["id"] == first["id"]


def test_api_returns_404_for_missing_report():
    response = client.get("/diagnostics/history/999999999")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_api_rejects_non_positive_report_id():
    response = client.get("/diagnostics/history/-1")

    assert response.status_code == 422
import os
import uuid

import pytest

from sedp.diagnostic_models import DiagnosticStatus
from sedp.report import DiagnosticReport
from sedp.repository import (
    get_connection,
    get_report,
    initialize_database,
    is_database_enabled,
    list_reports,
    save_report,
)


pytestmark = pytest.mark.skipif(
    os.getenv("SEDP_RUN_DB_TESTS") != "1",
    reason="Set SEDP_RUN_DB_TESTS=1 to run PostgreSQL integration tests.",
)


@pytest.fixture(scope="module", autouse=True)
def database():
    if not is_database_enabled():
        pytest.skip("PostgreSQL persistence is disabled.")

    initialize_database()


@pytest.fixture
def report():
    unique_id = uuid.uuid4().hex[:8]

    diagnostic_report = DiagnosticReport(
        equipment=f"SEDP-TEST-{unique_id}",
        status=DiagnosticStatus.FAULT,
        fault_code=f"TEST-{unique_id}",
        title="Repository integration test",
        priority=5,
        confidence=0.95,
        explanation="Test report for PostgreSQL persistence.",
        evidence=[],
        recommended_actions=["Inspect the test record."],
    )

    yield diagnostic_report

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM diagnostic_reports WHERE equipment = %s",
            (diagnostic_report.equipment,),
        )


def test_save_and_get_report(report):
    report_id = save_report(report)

    stored = get_report(report_id)

    assert stored is not None
    assert stored["id"] == report_id
    assert stored["report"]["equipment"] == report.equipment
    assert stored["report"]["status"] == "FAULT"
    assert stored["report"]["fault_code"] == report.fault_code


def test_list_reports_filters_by_equipment(report):
    report_id = save_report(report)

    results = list_reports(
        limit=20,
        equipment=report.equipment,
    )

    assert any(item["id"] == report_id for item in results)
    assert all(
        item["report"]["equipment"] == report.equipment
        for item in results
    )


def test_list_reports_filters_by_fault_code(report):
    report_id = save_report(report)

    results = list_reports(
        limit=20,
        fault_code=report.fault_code,
    )

    assert any(item["id"] == report_id for item in results)
    assert all(
        item["report"]["fault_code"] == report.fault_code
        for item in results
    )


def test_list_reports_supports_pagination(report):
    first_id = save_report(report)
    second_id = save_report(report)

    first_page = list_reports(
        limit=1,
        equipment=report.equipment,
    )
    second_page = list_reports(
        limit=1,
        offset=1,
        equipment=report.equipment,
    )

    assert len(first_page) == 1
    assert len(second_page) == 1
    assert first_page[0]["id"] == second_id
    assert second_page[0]["id"] == first_id


def test_get_report_returns_none_for_missing_id():
    assert get_report(-1) is None
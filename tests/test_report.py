import json
from pathlib import Path

import pytest

from sedp.diagnostic_models import DiagnosticResult, DiagnosticStatus
from sedp.diagnostics import DiagnosticEngine
from sedp.evidence import DiagnosticEvidence
from sedp.ingestion import load_events_from_json
from sedp.report import DiagnosticReport

@pytest.fixture
def cooling_result():
    return DiagnosticResult(
        status=DiagnosticStatus.FAULT,
        equipment="SEDP-SEM-001",
        subsystem="cooling",
        fault_code="COOL-002",
        title="Cooling system degradation detected",
        description="Cooling sequence indicates a degraded cooling condition.",
        confidence=0.98,
        priority=10,
        evidence=[
            DiagnosticEvidence(
                event_code="COOLING_PUMP_ON",
                description="Cooling pump activated",
            ),
            DiagnosticEvidence(
                event_code="COOLING_FLOW_LOW",
                description="Cooling flow below expected level",
                value=0.82,
                unit="L/min",
                severity="warning",
                elapsed_seconds=15,
            ),
            DiagnosticEvidence(
                event_code="COOLING_TEMP_HIGH",
                description="Cooling temperature above limit",
                value=35.0,
                unit="°C",
                severity="error",
                elapsed_seconds=15,
            ),
        ],
        recommended_actions=[
            "Check cooling pump operation.",
            "Inspect coolant flow.",
            "Verify coolant level.",
            "Check temperature sensor.",
        ],
    )

@pytest.fixture
def cooling_explanation():
    return (
        "The cooling pump was activated, followed 15 seconds later "
        "by low cooling flow, followed another 15 seconds later "
        "by high cooling temperature."
    )

def test_diagnostic_report_from_result():
    result = DiagnosticResult(
        status=DiagnosticStatus.FAULT,
        equipment="SEDP-SEM-001",
        subsystem="cooling",
        fault_code="COOL-002",
        title="Cooling system degradation detected",
        description="Cooling sequence indicates a degraded cooling condition.",
        confidence=0.98,
        priority=10,
        evidence=[
            DiagnosticEvidence(
                event_code="COOLING_PUMP_ON",
                description="Cooling pump activated",
            ),
            DiagnosticEvidence(
                event_code="COOLING_FLOW_LOW",
                description="Cooling flow below expected level",
                elapsed_seconds=15,
            ),
            DiagnosticEvidence(
                event_code="COOLING_TEMP_HIGH",
                description="Cooling temperature above limit",
                elapsed_seconds=15,
            ),
        ],
        recommended_actions=[
            "Check cooling pump operation.",
            "Inspect coolant flow.",
            "Verify coolant level.",
            "Check temperature sensor.",
        ],
    )

    report = DiagnosticReport.from_result(
        result,
        explanation=(
            "The cooling pump was activated, followed 15 seconds later "
            "by low cooling flow, followed another 15 seconds later "
            "by high cooling temperature."
        ),
    )

    assert report.equipment == "SEDP-SEM-001"
    assert report.status == DiagnosticStatus.FAULT
    assert report.fault_code == "COOL-002"
    assert report.priority == 10
    assert report.confidence == 0.98
    assert len(report.evidence) == 3
    assert report.evidence[1].elapsed_seconds == 15
    assert report.evidence[2].elapsed_seconds == 15
    assert len(report.recommended_actions) == 4

def test_diagnostic_report_to_text(
    cooling_result,
    cooling_explanation,
):
    report = DiagnosticReport.from_result(
        cooling_result,
        explanation=cooling_explanation,
    )

    text = report.to_text()

    assert "DIAGNOSTIC REPORT" in text
    assert "Equipment: SEDP-SEM-001" in text
    assert "Status: FAULT" in text
    assert "Fault code: COOL-002" in text
    assert "Title: Cooling system degradation detected" in text
    assert "Priority: 10" in text
    assert "Confidence: 98%" in text

    assert "Explanation:" in text
    assert "COOLING_PUMP_ON" in text
    assert "COOLING_FLOW_LOW (+15 s)" in text
    assert "COOLING_TEMP_HIGH (+15 s)" in text

    assert "Recommended actions:" in text
    assert "- Check cooling pump operation." in text
    assert "- Inspect coolant flow." in text

    text = report.to_text()

    assert "DIAGNOSTIC REPORT" in text
    assert "Equipment: SEDP-SEM-001" in text
    assert "Status: FAULT" in text
    assert "Fault code: COOL-002" in text
    assert "Title: Cooling system degradation detected" in text
    assert "Priority: 10" in text
    assert "Confidence: 98%" in text

    assert "Explanation:" in text
    assert "COOLING_PUMP_ON" in text
    assert "COOLING_FLOW_LOW (+15 s)" in text
    assert "COOLING_TEMP_HIGH (+15 s)" in text

    assert "Recommended actions:" in text
    assert "- Check cooling pump operation." in text
    assert "- Inspect coolant flow." in text

from pathlib import Path

from sedp.diagnostics import DiagnosticEngine
from sedp.ingestion import load_events_from_json

def test_diagnostic_report_from_real_cooling_sequence():
    events = load_events_from_json(
        Path("examples/cooling-fault-sequence.json")
    )

    engine = DiagnosticEngine()
    result = engine.diagnose(events)

    report = DiagnosticReport.from_result(
        result,
        explanation=(
            "The cooling pump was activated, followed 15 seconds later "
            "by low cooling flow, followed another 15 seconds later "
            "by high cooling temperature."
        ),
    )

    text = report.to_text()

    assert report.equipment == "SEDP-SEM-001"
    assert report.fault_code == "COOL-002"
    assert report.priority == 10
    assert report.confidence == 0.98

    assert "DIAGNOSTIC REPORT" in text
    assert "Equipment: SEDP-SEM-001" in text
    assert "Status: FAULT" in text
    assert "Fault code: COOL-002" in text
    assert "Priority: 10" in text
    assert "Confidence: 98%" in text

    assert "COOLING_PUMP_ON" in text
    assert "COOLING_FLOW_LOW (+15 s)" in text
    assert "COOLING_TEMP_HIGH (+15 s)" in text

def test_diagnostic_report_to_dict(
    cooling_result,
    cooling_explanation,
):
    report = DiagnosticReport.from_result(
        cooling_result,
        explanation=cooling_explanation,
    )

    data = report.to_dict()

    assert data["equipment"] == "SEDP-SEM-001"
    assert data["status"] == "FAULT"
    assert data["fault_code"] == "COOL-002"
    assert data["title"] == "Cooling system degradation detected"
    assert data["priority"] == 10
    assert data["confidence"] == 0.98

    assert data["explanation"] == cooling_explanation

    assert len(data["evidence"]) == 3

    assert data["evidence"][0]["event_code"] == "COOLING_PUMP_ON"

    assert data["evidence"][1]["event_code"] == "COOLING_FLOW_LOW"
    assert data["evidence"][1]["value"] == 0.82
    assert data["evidence"][1]["unit"] == "L/min"
    assert data["evidence"][1]["severity"] == "warning"
    assert data["evidence"][1]["elapsed_seconds"] == 15

    assert data["evidence"][2]["event_code"] == "COOLING_TEMP_HIGH"
    assert data["evidence"][2]["value"] == 35.0
    assert data["evidence"][2]["unit"] == "°C"
    assert data["evidence"][2]["severity"] == "error"
    assert data["evidence"][2]["elapsed_seconds"] == 15

    assert data["recommended_actions"] == [
        "Check cooling pump operation.",
        "Inspect coolant flow.",
        "Verify coolant level.",
        "Check temperature sensor.",
    ]

    data = report.to_dict()

    assert data["equipment"] == "SEDP-SEM-001"
    assert data["status"] == "FAULT"
    assert data["fault_code"] == "COOL-002"
    assert data["title"] == "Cooling system degradation detected"
    assert data["priority"] == 10
    assert data["confidence"] == 0.98

    assert data["explanation"].startswith(
        "The cooling pump was activated"
    )

    assert len(data["evidence"]) == 3

    assert data["evidence"][0]["event_code"] == "COOLING_PUMP_ON"

    assert data["evidence"][1]["event_code"] == "COOLING_FLOW_LOW"
    assert data["evidence"][1]["value"] == 0.82
    assert data["evidence"][1]["unit"] == "L/min"
    assert data["evidence"][1]["severity"] == "warning"
    assert data["evidence"][1]["elapsed_seconds"] == 15

    assert data["evidence"][2]["event_code"] == "COOLING_TEMP_HIGH"
    assert data["evidence"][2]["value"] == 35.0
    assert data["evidence"][2]["unit"] == "°C"
    assert data["evidence"][2]["severity"] == "error"
    assert data["evidence"][2]["elapsed_seconds"] == 15

    assert data["recommended_actions"] == [
        "Check cooling pump operation.",
        "Inspect coolant flow.",
        "Verify coolant level.",
        "Check temperature sensor.",
    ]

import json

def test_diagnostic_report_to_json(
    cooling_result,
    cooling_explanation,
):
    report = DiagnosticReport.from_result(
        cooling_result,
        explanation=cooling_explanation,
    )

    json_text = report.to_json()
    data = json.loads(json_text)

    assert data["equipment"] == "SEDP-SEM-001"
    assert data["status"] == "FAULT"
    assert data["fault_code"] == "COOL-002"
    assert data["priority"] == 10
    assert data["confidence"] == 0.98

    assert len(data["evidence"]) == 3

    assert data["evidence"][1]["event_code"] == "COOLING_FLOW_LOW"
    assert data["evidence"][1]["elapsed_seconds"] == 15

    assert data["evidence"][2]["event_code"] == "COOLING_TEMP_HIGH"
    assert data["evidence"][2]["elapsed_seconds"] == 15

    assert len(data["recommended_actions"]) == 4
    
    json_text = report.to_json()

    data = json.loads(json_text)

    assert data["equipment"] == "SEDP-SEM-001"
    assert data["status"] == "FAULT"
    assert data["fault_code"] == "COOL-002"
    assert data["priority"] == 10
    assert data["confidence"] == 0.98

    assert len(data["evidence"]) == 3

    assert data["evidence"][1]["event_code"] == "COOLING_FLOW_LOW"
    assert data["evidence"][1]["elapsed_seconds"] == 15

    assert data["evidence"][2]["event_code"] == "COOLING_TEMP_HIGH"
    assert data["evidence"][2]["elapsed_seconds"] == 15

    assert len(data["recommended_actions"]) == 4

    
def test_diagnostic_report_with_insufficient_data():
    engine = DiagnosticEngine()

    result = engine.diagnose([])

    report = DiagnosticReport.from_result(
        result,
        explanation="No equipment events were provided.",
    )

    data = report.to_dict()

    assert data["equipment"] == "unknown"
    assert data["status"] == "UNKNOWN"
    assert data["fault_code"] is None
    assert data["title"] == "Insufficient data"
    assert data["priority"] == 0
    assert data["confidence"] == 0.0
    assert data["explanation"] == "No equipment events were provided."
    assert data["evidence"] == []
    assert data["recommended_actions"] == []


def test_diagnostic_report_with_normal_status():
    result = DiagnosticResult(
        status=DiagnosticStatus.NORMAL,
        equipment="SEDP-SEM-001",
        subsystem="cooling",
        fault_code=None,
        title="Cooling system operating normally",
        description="No cooling abnormalities detected.",
        confidence=0.95,
        priority=0,
        evidence=[],
        recommended_actions=[],
    )

    report = DiagnosticReport.from_result(
        result,
        explanation="No cooling abnormalities were detected.",
    )

    data = report.to_dict()

    assert data["equipment"] == "SEDP-SEM-001"
    assert data["status"] == "NORMAL"
    assert data["fault_code"] is None
    assert data["title"] == "Cooling system operating normally"
    assert data["priority"] == 0
    assert data["confidence"] == 0.95
    assert data["evidence"] == []
    assert data["recommended_actions"] == []


def test_diagnostic_report_json_round_trip(cooling_result, cooling_explanation):
    report = DiagnosticReport.from_result(
        cooling_result,
        explanation=cooling_explanation,
    )

    json_output = report.to_json()
    data = json.loads(json_output)

    assert data["equipment"] == cooling_result.equipment
    assert data["status"] == cooling_result.status.value.upper()
    assert data["fault_code"] == cooling_result.fault_code
    assert data["priority"] == cooling_result.priority
    assert data["confidence"] == cooling_result.confidence
    assert data["explanation"] == cooling_explanation

    assert len(data["evidence"]) == len(cooling_result.evidence)

    assert data["evidence"][1]["event_code"] == "COOLING_FLOW_LOW"
    assert data["evidence"][1]["elapsed_seconds"] == 15

    assert data["evidence"][2]["event_code"] == "COOLING_TEMP_HIGH"
    assert data["evidence"][2]["elapsed_seconds"] == 15

    assert data["recommended_actions"] == cooling_result.recommended_actions
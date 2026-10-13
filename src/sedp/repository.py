
import os

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from .report import DiagnosticReport


load_dotenv()


def is_database_enabled() -> bool:
    return os.getenv("SEDP_DB_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
    }



def get_connection() -> psycopg.Connection:
    password = os.getenv("SEDP_DB_PASSWORD")

    if not password:
        raise RuntimeError(
            "SEDP_DB_PASSWORD is not configured in the environment or .env file."
        )

    port_value = os.getenv("SEDP_DB_PORT", "5432")

    try:
        port = int(port_value)
    except ValueError as exc:
        raise RuntimeError(
            "SEDP_DB_PORT must be a valid integer."
        ) from exc

    if not 1 <= port <= 65535:
        raise RuntimeError(
            "SEDP_DB_PORT must be between 1 and 65535."
        )

    return psycopg.connect(
        host=os.getenv("SEDP_DB_HOST", "localhost"),
        port=port,
        dbname=os.getenv("SEDP_DB_NAME", "sedp"),
        user=os.getenv("SEDP_DB_USER", "sedp_user"),
        password=password,
    )


    
def initialize_database() -> None:
    """Create the diagnostic history table if it does not exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnostic_reports (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                equipment TEXT NOT NULL,
                status TEXT NOT NULL,
                fault_code TEXT,
                priority INTEGER NOT NULL,
                confidence DOUBLE PRECISION NOT NULL,
                report_data JSONB NOT NULL
            )
            """
        )


def save_report(report: DiagnosticReport) -> int:
    """Save a report and return its database identifier."""
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO diagnostic_reports (
                equipment,
                status,
                fault_code,
                priority,
                confidence,
                report_data
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                report.equipment,
                report.status.value.upper(),
                report.fault_code,
                report.priority,
                report.confidence,
                Jsonb(report.to_dict()),
            ),
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "The database did not return the report identifier."
            )

        return row[0]


def list_reports(
    limit: int = 20,
    offset: int = 0,
    equipment: str | None = None,
    fault_code: str | None = None,
) -> list[dict]:
    """List recent diagnostic reports with optional filters."""
    conditions = []
    parameters = []

    if equipment:
        conditions.append("equipment = %s")
        parameters.append(equipment)

    if fault_code:
        conditions.append("fault_code = %s")
        parameters.append(fault_code)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    query = f"""
        SELECT id, created_at, report_data
        FROM diagnostic_reports
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s
    """

    parameters.extend([limit, offset])

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [
        {
            "id": row[0],
            "created_at": row[1].isoformat(),
            "report": row[2],
        }
        for row in rows
    ]


def get_report(report_id: int) -> dict | None:
    """Retrieve one diagnostic report by its database identifier."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, created_at, report_data
            FROM diagnostic_reports
            WHERE id = %s
            """,
            (report_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "created_at": row[1].isoformat(),
        "report": row[2],
    }
from .diagnostic_models import DiagnosticResult


def explain_diagnosis(result: DiagnosticResult) -> str:
    """Generate a human-readable explanation of a diagnosis."""

    if result.sequence_evidence is not None:
        events = result.sequence_evidence.events

        if not events:
            return result.description or "No diagnostic explanation available."

        explanation = result.title or "Diagnostic sequence detected"

        explanation += ": "

        explanation += events[0].description

        for event in events[1:]:
            if event.elapsed_seconds is not None:
                explanation += (
                    f", followed {event.elapsed_seconds:.0f} seconds later "
                )

            explanation += event.description.lower()

        return explanation

    if result.description:
        return result.description

    return "No diagnostic explanation available."
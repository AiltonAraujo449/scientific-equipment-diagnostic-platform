# Diagnostic Priority Model

## Overview

The SEDP uses two independent attributes to describe a diagnostic result:

* `confidence`: indicates how confident the diagnostic engine is that the diagnosis is correct.
* `priority`: indicates the operational importance of the detected condition.

These values must not be derived from each other.

A diagnosis may have high confidence but low operational priority, or lower confidence but high operational priority.

## Priority scale

The `priority` value is an integer. Higher values represent higher operational priority.

| Priority | Meaning                         |
| -------: | ------------------------------- |
|        0 | Undefined / not specified       |
|      1–4 | Low operational priority        |
|      5–9 | Operational fault               |
|    10–19 | High-priority or systemic fault |
|      20+ | Critical condition              |

The scale is intentionally numeric so that future diagnostic rules can introduce intermediate priority levels without requiring changes to the data model.

## Current diagnostic rules

| Rule                   | Fault code | Priority | Confidence |
| ---------------------- | ---------- | -------: | ---------: |
| Vacuum pressure        | `VAC-001`  |        5 |       0.95 |
| Cooling temperature    | `COOL-001` |        5 |       0.95 |
| Cooling fault sequence | `COOL-002` |       10 |       0.98 |

The values above describe the current implementation and may evolve as additional domain rules are introduced.

## Diagnostic selection

When multiple diagnoses are detected, `DiagnosticEngine` selects the most relevant diagnosis using the following order:

1. Higher `priority`
2. Higher `confidence` when priorities are equal

For example:

```text
Diagnosis A
priority   = 10
confidence = 0.80

Diagnosis B
priority   = 5
confidence = 0.99
```

Diagnosis A is selected because its operational priority is higher.

If priorities are equal:

```text
Diagnosis A
priority   = 10
confidence = 0.80

Diagnosis B
priority   = 10
confidence = 0.95
```

Diagnosis B is selected because confidence is used as the tie-breaker.

## Design principle

`priority` answers:

> Which condition should receive attention first?

`confidence` answers:

> How certain is the diagnostic engine about this conclusion?

The SEDP keeps these concepts independent to support future diagnostic workflows, remote assistance, field-engineer prioritization, and eventual predictive-maintenance capabilities.

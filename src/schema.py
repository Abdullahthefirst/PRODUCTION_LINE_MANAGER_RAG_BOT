ALIASES = {
    "line_id": [
        "line id", "line", "production line", "line name", "production_line",
        "line no", "line number"
    ],
    "supervisor": [
        "supervisor", "line supervisor", "manager", "responsible person",
        "supervisor name", "line incharge", "line in charge"
    ],
    "product": [
        "product", "item", "sku", "product name", "item name", "style",
        "product code"
    ],
    "week": [
        "week", "week no", "week number", "production week", "week id"
    ],
    "week_start": [
        "week start", "week starting", "date", "start date", "week date"
    ],
    "target_units": [
        "target units", "target", "weekly target", "planned units", "plan",
        "planned production", "production target", "weekly goal",
        "production plan qty", "planned output", "qty target", "target qty",
        "target quantity", "plan qty"
    ],
    "actual_units": [
        "actual units", "actual", "production", "output", "actual production",
        "produced units", "actual output", "production qty", "produced qty",
        "completed units", "quantity produced"
    ],
    "downtime_hours": [
        "downtime hours", "downtime hrs", "downtime", "down time hours",
        "stoppage hours", "lost hours"
    ],
    "defect_units": [
        "defect units", "defects", "rejected units", "rejects", "scrap",
        "rejection", "rejected qty", "defect qty", "waste units"
    ],
    "status": [
        "status", "line status", "production status", "state"
    ],
    "machine_id": [
        "machine id", "machine", "equipment id", "machine no",
        "machine number", "equipment", "equipment no"
    ],
    "machine_type": [
        "machine type", "equipment type", "type", "machine category"
    ],
    "issue": [
        "issue", "problem", "fault", "machine issue", "issue description",
        "fault description", "breakdown reason", "downtime reason"
    ],
    "severity": [
        "severity", "priority", "criticality"
    ],
    "downtime_minutes": [
        "downtime minutes", "downtime min", "minutes down",
        "stoppage minutes", "down time minutes", "lost minutes"
    ],
    "action_taken": [
        "action taken", "action", "resolution", "maintenance action",
        "corrective action", "repair action"
    ],
    "resolved": [
        "resolved", "closed", "fixed", "is resolved"
    ],
    "quarter": [
        "quarter", "qtr", "production quarter"
    ],
    "quarter_target": [
        "quarter target", "quarterly target", "quarter target units",
        "quarterly target units"
    ],
}

CANONICAL_GROUPS = {
    "weekly_production": [
        "line_id", "supervisor", "product", "week", "week_start",
        "target_units", "actual_units", "downtime_hours",
        "defect_units", "status"
    ],
    "machine_issues": [
        "line_id", "machine_id", "machine_type", "issue", "severity",
        "downtime_minutes", "action_taken", "resolved"
    ],
    "quarter_targets": [
        "quarter", "product", "quarter_target"
    ],
    "production_lines": [
        "line_id", "supervisor", "product", "status"
    ],
}

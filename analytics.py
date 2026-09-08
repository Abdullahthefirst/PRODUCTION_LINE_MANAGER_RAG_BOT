import pandas as pd
import numpy as np

def _concat_matching(tables, required_any):
    frames = []
    for name, df in tables.items():
        if any(col in df.columns for col in required_any):
            temp = df.copy()
            temp["_source"] = name
            frames.append(temp)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)

def _sum_numeric(df, col):
    if col not in df.columns:
        return 0.0
    s = pd.to_numeric(df[col], errors="coerce")
    value = s.sum(min_count=1)
    return 0.0 if pd.isna(value) else float(value)

def build_analysis(tables):
    prod = _concat_matching(tables, ["target_units", "actual_units"])
    issues = _concat_matching(tables, ["machine_id", "issue", "downtime_minutes"])
    quarter = _concat_matching(tables, ["quarter_target", "quarter"])

    result = {
        "production": prod,
        "issues": issues,
        "quarter": quarter,
        "kpis": {},
        "line_summary": pd.DataFrame(),
        "machine_summary": pd.DataFrame(),
        "issue_summary": pd.DataFrame(),
        "weekly_summary": pd.DataFrame(),
        "deterministic_findings": [],
    }

    findings = []

    if not prod.empty:
        # Convert only columns that actually exist.
        for c in ["target_units", "actual_units", "downtime_hours", "defect_units"]:
            if c in prod.columns:
                prod[c] = pd.to_numeric(prod[c], errors="coerce")

        target = _sum_numeric(prod, "target_units")
        actual = _sum_numeric(prod, "actual_units")
        achievement = (actual / target * 100) if target else 0.0

        result["kpis"].update({
            "total_target": target,
            "total_actual": actual,
            "achievement_pct": achievement,
            "variance": actual - target if target else 0.0,
        })

        # Line summary: only aggregate columns that exist.
        if "line_id" in prod.columns:
            agg = {}
            if "target_units" in prod.columns:
                agg["target_units"] = "sum"
            if "actual_units" in prod.columns:
                agg["actual_units"] = "sum"
            if "downtime_hours" in prod.columns:
                agg["downtime_hours"] = "sum"
            if "defect_units" in prod.columns:
                agg["defect_units"] = "sum"

            if agg:
                line = prod.groupby("line_id", dropna=False).agg(agg).reset_index()

                if "target_units" in line.columns and "actual_units" in line.columns:
                    line["achievement_pct"] = np.where(
                        line["target_units"] > 0,
                        line["actual_units"] / line["target_units"] * 100,
                        0,
                    )
                    line["variance"] = line["actual_units"] - line["target_units"]
                elif "actual_units" in line.columns:
                    line["achievement_pct"] = np.nan
                    line["variance"] = np.nan

                if "supervisor" in prod.columns:
                    sups = (
                        prod.groupby("line_id")["supervisor"]
                        .agg(lambda s: s.dropna().astype(str).iloc[-1] if len(s.dropna()) else "")
                        .reset_index()
                    )
                    line = line.merge(sups, on="line_id", how="left")

                if "achievement_pct" in line.columns and line["achievement_pct"].notna().any():
                    line = line.sort_values("achievement_pct")
                    worst = line.dropna(subset=["achievement_pct"]).iloc[0]
                    best = line.dropna(subset=["achievement_pct"]).iloc[-1]
                    findings.append(
                        f"{worst['line_id']} is the lowest-performing line at "
                        f"{worst['achievement_pct']:.1f}% of target."
                    )
                    findings.append(
                        f"{best['line_id']} is the strongest line at "
                        f"{best['achievement_pct']:.1f}% of target."
                    )

                result["line_summary"] = line

        # Weekly summary: don't assume both target and actual exist.
        if "week" in prod.columns:
            weekly_cols = [c for c in ["target_units", "actual_units"] if c in prod.columns]
            if weekly_cols:
                weekly = prod.groupby("week", dropna=False)[weekly_cols].sum().reset_index()

                if "target_units" in weekly.columns and "actual_units" in weekly.columns:
                    weekly["achievement_pct"] = np.where(
                        weekly["target_units"] > 0,
                        weekly["actual_units"] / weekly["target_units"] * 100,
                        0,
                    )
                result["weekly_summary"] = weekly

        if "defect_units" in prod.columns and actual:
            defects = _sum_numeric(prod, "defect_units")
            result["kpis"]["defect_rate_pct"] = defects / actual * 100

        if "downtime_hours" in prod.columns:
            result["kpis"]["downtime_hours"] = _sum_numeric(prod, "downtime_hours")

    if not issues.empty:
        if "downtime_minutes" in issues.columns:
            issues["downtime_minutes"] = pd.to_numeric(
                issues["downtime_minutes"], errors="coerce"
            ).fillna(0)

        if "machine_id" in issues.columns:
            machine = issues.groupby("machine_id").size().reset_index(name="issue_count")

            if "downtime_minutes" in issues.columns:
                d = issues.groupby("machine_id")["downtime_minutes"].sum().reset_index()
                machine = machine.merge(d, on="machine_id", how="left")

            if "line_id" in issues.columns:
                l = (
                    issues.groupby("machine_id")["line_id"]
                    .agg(lambda s: s.dropna().astype(str).iloc[-1] if len(s.dropna()) else "")
                    .reset_index()
                )
                machine = machine.merge(l, on="machine_id", how="left")

            sort_col = "downtime_minutes" if "downtime_minutes" in machine.columns else "issue_count"
            machine = machine.sort_values([sort_col, "issue_count"], ascending=False)
            result["machine_summary"] = machine

            if len(machine):
                top = machine.iloc[0]
                downtime_txt = (
                    f" and {top.get('downtime_minutes', 0):.0f} minutes of logged downtime"
                    if "downtime_minutes" in machine.columns
                    else ""
                )
                findings.append(
                    f"Machine {top['machine_id']} has the highest recorded impact with "
                    f"{int(top['issue_count'])} issues{downtime_txt}."
                )

        if "issue" in issues.columns:
            issue_summary = (
                issues.groupby("issue").size().reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            result["issue_summary"] = issue_summary
            if len(issue_summary):
                findings.append(
                    f"The most frequent issue type is '{issue_summary.iloc[0]['issue']}' "
                    f"({int(issue_summary.iloc[0]['count'])} events)."
                )

    # Cross-reference weak lines with recurring machines only when achievement data exists.
    line_summary = result["line_summary"]
    machine_summary = result["machine_summary"]
    if (
        not line_summary.empty
        and not machine_summary.empty
        and "line_id" in machine_summary.columns
        and "achievement_pct" in line_summary.columns
        and line_summary["achievement_pct"].notna().any()
    ):
        weak_lines = (
            line_summary.dropna(subset=["achievement_pct"])
            .sort_values("achievement_pct")
            .head(min(2, len(line_summary)))["line_id"]
            .astype(str)
        )
        weak = set(weak_lines)

        machine_on_weak = machine_summary[
            machine_summary["line_id"].astype(str).isin(weak)
        ]

        if len(machine_on_weak):
            m = machine_on_weak.iloc[0]
            findings.append(
                f"Prioritize inspection of {m['machine_id']} on {m['line_id']}; "
                f"it is a recurring issue source on a weaker production line."
            )

    result["deterministic_findings"] = findings
    return result

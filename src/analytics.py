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
        for c in ["target_units", "actual_units", "downtime_hours", "defect_units"]:
            if c in prod.columns:
                prod[c] = pd.to_numeric(prod[c], errors="coerce")

        target = prod.get("target_units", pd.Series(dtype=float)).sum(min_count=1)
        actual = prod.get("actual_units", pd.Series(dtype=float)).sum(min_count=1)
        target = 0 if pd.isna(target) else float(target)
        actual = 0 if pd.isna(actual) else float(actual)
        achievement = (actual / target * 100) if target else 0
        result["kpis"].update({
            "total_target": target,
            "total_actual": actual,
            "achievement_pct": achievement,
            "variance": actual - target,
        })

        if "line_id" in prod.columns:
            agg = {"target_units": "sum", "actual_units": "sum"}
            if "downtime_hours" in prod.columns: agg["downtime_hours"] = "sum"
            if "defect_units" in prod.columns: agg["defect_units"] = "sum"
            line = prod.groupby("line_id", dropna=False).agg(agg).reset_index()
            line["achievement_pct"] = np.where(line["target_units"] > 0, line["actual_units"] / line["target_units"] * 100, 0)
            line["variance"] = line["actual_units"] - line["target_units"]

            if "supervisor" in prod.columns:
                sups = prod.groupby("line_id")["supervisor"].agg(lambda s: s.dropna().astype(str).iloc[-1] if len(s.dropna()) else "").reset_index()
                line = line.merge(sups, on="line_id", how="left")
            result["line_summary"] = line.sort_values("achievement_pct")

            if len(line):
                worst = line.iloc[0]
                best = line.iloc[-1]
                findings.append(f"{worst['line_id']} is the lowest-performing line at {worst['achievement_pct']:.1f}% of target.")
                findings.append(f"{best['line_id']} is the strongest line at {best['achievement_pct']:.1f}% of target.")

        if "week" in prod.columns:
            agg = prod.groupby("week", dropna=False)[["target_units", "actual_units"]].sum().reset_index()
            agg["achievement_pct"] = np.where(agg["target_units"] > 0, agg["actual_units"]/agg["target_units"]*100, 0)
            result["weekly_summary"] = agg

        if "defect_units" in prod.columns and actual:
            defects = prod["defect_units"].sum()
            result["kpis"]["defect_rate_pct"] = defects / actual * 100
        if "downtime_hours" in prod.columns:
            result["kpis"]["downtime_hours"] = prod["downtime_hours"].sum()

    if not issues.empty:
        if "downtime_minutes" in issues.columns:
            issues["downtime_minutes"] = pd.to_numeric(issues["downtime_minutes"], errors="coerce").fillna(0)
        if "machine_id" in issues.columns:
            agg = {"machine_id": "size"}
            machine = issues.groupby("machine_id").size().reset_index(name="issue_count")
            if "downtime_minutes" in issues.columns:
                d = issues.groupby("machine_id")["downtime_minutes"].sum().reset_index()
                machine = machine.merge(d, on="machine_id", how="left")
            if "line_id" in issues.columns:
                l = issues.groupby("machine_id")["line_id"].agg(lambda s: s.dropna().astype(str).iloc[-1] if len(s.dropna()) else "").reset_index()
                machine = machine.merge(l, on="machine_id", how="left")
            result["machine_summary"] = machine.sort_values(
                ["downtime_minutes" if "downtime_minutes" in machine.columns else "issue_count", "issue_count"],
                ascending=False
            )
            top = result["machine_summary"].iloc[0]
            downtime_txt = f" and {top.get('downtime_minutes', 0):.0f} minutes of logged downtime" if "downtime_minutes" in top else ""
            findings.append(f"Machine {top['machine_id']} has the highest recorded impact with {int(top['issue_count'])} issues{downtime_txt}.")

        if "issue" in issues.columns:
            issue_summary = issues.groupby("issue").size().reset_index(name="count").sort_values("count", ascending=False)
            result["issue_summary"] = issue_summary
            if len(issue_summary):
                findings.append(f"The most frequent issue type is '{issue_summary.iloc[0]['issue']}' ({int(issue_summary.iloc[0]['count'])} events).")

    # Cross-reference problematic lines and machines.
    if not result["line_summary"].empty and not result["machine_summary"].empty and "line_id" in result["machine_summary"].columns:
        weak = set(result["line_summary"].head(min(2, len(result["line_summary"])))["line_id"].astype(str))
        machine_on_weak = result["machine_summary"][result["machine_summary"]["line_id"].astype(str).isin(weak)]
        if len(machine_on_weak):
            m = machine_on_weak.iloc[0]
            findings.append(f"Prioritize inspection of {m['machine_id']} on {m['line_id']}; it is a recurring issue source on a weaker production line.")

    result["deterministic_findings"] = findings
    return result

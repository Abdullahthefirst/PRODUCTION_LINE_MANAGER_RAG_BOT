import re
import pandas as pd

def clean_col(name):
    return re.sub(r"\s+", " ", str(name).strip().lower().replace("_", " ").replace("-", " "))

def best_alias_map(columns, aliases):
    cleaned = {c: clean_col(c) for c in columns}
    mapping = {}
    for canonical, names in aliases.items():
        options = {clean_col(canonical), *(clean_col(x) for x in names)}
        for original, cclean in cleaned.items():
            if cclean in options:
                mapping[original] = canonical
                break
    return mapping

def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def safe_pct(n, d):
    try:
        if d is None or float(d) == 0:
            return 0.0
        return float(n) / float(d)
    except Exception:
        return 0.0

def dataframe_to_records_text(name, df, max_rows=5000):
    out = []
    for idx, row in df.head(max_rows).iterrows():
        pairs = []
        for col, val in row.items():
            if pd.isna(val):
                continue
            pairs.append(f"{col}: {val}")
        if pairs:
            out.append(f"Source table {name}, row {idx + 1}. " + "; ".join(pairs))
    return out

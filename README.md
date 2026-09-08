# FactoryOps AI — corrected Streamlit build

Session-only production intelligence dashboard using:

- Streamlit
- Gemini 3.6 Flash (`gemini-3.6-flash`)
- Gemini text embeddings (`gemini-embedding-001`)
- FAISS
- Pandas
- Plotly

## Corrections in this build

1. **Gemini key handling**
   - The key gate validates credentials with the Models API rather than a generation request.
   - A 503/high-demand response is not treated as a false key.
   - The key screen returns only for genuine authentication failures.

2. **Gemini 3.6 Flash**
   - The project keeps the stable model ID `gemini-3.6-flash`.
   - If the key/project/region does not expose that model, the app does not crash or invalidate the key.
   - Deterministic dashboard analysis continues to work.
   - Generation calls retry temporary 429/5xx errors with exponential backoff.

3. **Incomplete / missing file data**
   - Missing target, actual, week, machine, issue, supervisor or downtime columns no longer crash charts.
   - Empty or partly-readable files are reported as data gaps.
   - Analytics are stored before embedding begins, so a Gemini embedding failure does not destroy the dashboard result.
   - If no searchable chunks exist, the dashboard still loads and explains that RAG is unavailable.

4. **Dashboard**
   - Null-safe KPI cards and charts.
   - Weekly production chart only renders available series.
   - Line and machine tables only use existing columns.
   - Interactive line filter.
   - Data-readiness panel.
   - Calculated machine/production alerts.
   - Uploaded-data preview.
   - AI analysis is optional and does not block local analytics.

5. **FAISS**
   - FAISS is still session-only and in memory.
   - Failed embedding/index creation can be retried from Upload Data.

## Run locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

For Streamlit Community Cloud, point the app entry file to:

```text
app.py
```

Python 3.11 or 3.12 is recommended for the smoothest compatibility with FAISS and ML packages.

## Main files

```text
app.py
src/
  auth.py
  gemini_client.py
  ingestion.py
  analytics.py
  charts.py
  dashboard.py
  rag_engine.py
  rag.py
  ai_analysis.py
  schema.py
  data_utils.py
  state.py
  styles.py
```

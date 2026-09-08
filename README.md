# FactoryOps AI

A session-only Streamlit dashboard for mid-sized factory production analysis.

## Core features

- Gemini API key gate shown at startup.
- The API-key section disappears after successful validation.
- It reappears only when the app detects a Gemini authentication/key failure.
- Upload multiple CSV, Excel, JSON, TXT, Markdown, PDF, and DOCX files.
- Normalize common production, line, supervisor, target, machine, issue, downtime and defect fields.
- Report missing / insufficient information before relying on it.
- Calculate target vs actual, variance, line performance, downtime and recurring machine issues.
- Interactive Plotly dashboard.
- Gemini 3.6 Flash management analysis and suggestions.
- In-memory FAISS semantic retrieval.
- "Ask the Factory" RAG chat with retrieved evidence.
- No application database; uploaded/processed data stays in the Streamlit session.

## Architecture

```text
Uploads
  ↓
Extraction
  ↓
Column normalization
  ↓
Data-quality / sufficiency check
  ↓
Deterministic analytics ─────────────→ Dashboard charts + KPI cards
  ↓
Chunk generation
  ↓
Gemini embeddings
  ↓
In-memory FAISS
  ↓
RAG retrieval ──→ Gemini 3.6 Flash ──→ Factory Q&A / recommendations
```

The app deliberately calculates numeric facts in Python instead of asking the LLM to infer sums,
rankings or target variances from vector-search results.

## Local setup

Use Python 3.11 or 3.12 for the easiest FAISS compatibility.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

The app asks for the Gemini API key inside the UI, so a Streamlit secret is not required.

## Streamlit Community Cloud deployment

1. Create a GitHub repository.
2. Upload this project with `app.py`, `requirements.txt`, `src/`, and `.streamlit/` at the repository root.
3. In Streamlit Community Cloud, create an app from the repository.
4. Set the entrypoint to `app.py`.
5. Choose a compatible Python version (3.11 or 3.12 recommended here).
6. Deploy.
7. Open the app and enter a Gemini API key.

## Gemini models used

Generation:
- `gemini-3.6-flash`

Embeddings:
- `gemini-embedding-001`

The model IDs are isolated in `src/gemini_client.py`, so changing models later takes one edit.

## Expected useful fields

The loader accepts different column names and maps common aliases. Best results come from data that
contains some of:

- quarter / quarter target
- week / week start
- production line
- line supervisor
- product
- weekly target
- actual production
- downtime
- defect / reject units
- machine ID / type
- machine issue
- issue severity
- action taken
- resolved status

## Important MVP limitations

- "Any file" really means the supported readable business formats above. Scanned PDFs/images need OCR
  or Gemini multimodal extraction, which is intentionally not included in this lightweight MVP.
- FAISS is in memory. A Streamlit rerun keeps it in the session, but a lost/restarted session requires
  the user to upload/process the data again.
- Automatic alias-based normalization is reliable for common spreadsheets, but very unusual schemas
  may need an additional Gemini structured-extraction step.
- Recommendations are decision support, not automatic maintenance commands.

# Survey Intake Case Study — Part 1

This repo contains **both** the Flask API and a small **HTML form** that submits JSON to it.

## Project Structure

```
survey-intake-case-study-part1/
├─ app.py                # Flask API (POST /v1/survey)
├─ models.py             # Pydantic v1 schemas (validation)
├─ storage.py            # Append-only JSON Lines helper
├─ requirements.txt
├─ frontend/
│  ├─ index.html         # Survey form (vanilla HTML + fetch)
│  └─ styles.css
├─ data/                 # Will contain survey.ndjson after submissions
└─ tests/
   └─ test_api.py        # Minimal API tests
```

---

## Step-by-step Setup (Local)

1. **Clone & enter**
   ```bash
   git clone <your-fork-url> survey-intake-case-study-part1
   cd survey-intake-case-study-part1
   ```

2. **Create a virtualenv & install deps**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run tests (optional but recommended)**
   ```bash
   pytest -q
   ```

4. **Start the API**
   ```bash
   python app.py
   # -> listening on http://127.0.0.1:5000
   ```

5. **Open the HTML form**
   - EITHER open `frontend/index.html` directly in your browser (double-click the file),
   - OR run a tiny static server from the `frontend/` folder:
     ```bash
     cd frontend
     python -m http.server 8000
     # visit http://127.0.0.1:8000
     ```

> **Why does the form work if served separately?**  
> We enabled permissive CORS on the Flask app so the static page can POST across origins during development. In production, restrict CORS to approved origins.

---

## End-to-end Test

Fill out the form and click **Submit**. On success you’ll see:
- A **201** response on the network tab and
- A green success message.

Check the stored data:
```bash
tail -n1 data/survey.ndjson | jq
```

You should see your submission with server-added fields:
```json
{"name":"Ava","email":"ava@example.com","age":22,"consent":true,"rating":4,"comments":"Loved it!","source":"homepage","received_at":"2025-01-01T00:00:00Z","ip":"127.0.0.1"}
```

---

## Anatomy of `frontend/index.html` (line-by-line)

- `<!DOCTYPE html>` and `<html lang="en">`: HTML5 doc & language hint.  
- `<meta charset="UTF-8">`: UTF‑8 so emojis/accents work.  
- `<meta name="viewport" ...>`: mobile-friendly scaling.  
- `<link rel="stylesheet" href="./styles.css">`: styles.  
- `<form id="survey-form" novalidate>`: we handle validation & messages ourselves (JS + server).  
- Inputs:
  - `name` (text), `email` (email), `age` (number), `consent` (checkbox), `rating` (select), `comments` (textarea).
  - Hidden `source` field (defaults to `"homepage"`).
- `<section id="result" ...>`: where we display success/error messages.  
- Script:
  - `form.addEventListener("submit", ...)`: intercept submit, `preventDefault()`.
  - `FormData(form)` → build a JS object `payload`.
  - **Type coercion**: `Number(...)` for `age` & `rating`, `checkbox==="on"` → boolean.
  - `fetch("http://127.0.0.1:5000/v1/survey", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)})`
  - If `res.ok` → show green message and `form.reset()`.
  - Else → show detailed error (422 validation errors include field-level info from Pydantic).
  - Finally → re-enable the submit button.

---

## Anatomy of `app.py`

- `app = Flask(__name__)` instantiates the app (import name used for defaults).
- `CORS(app, resources={r"/v1/*": {"origins": "*"}})` enables cross-origin fetches for dev.
- `@app.post("/v1/survey")` handles JSON POST.
  - `request.get_json(silent=True)`: returns `None` if not valid JSON → **400**.
  - `SurveySubmission(**payload)`: Pydantic v1 validation → raises `ValidationError` → **422** with details.
  - Enrich with `received_at` (UTC) and `ip`.
  - `append_json_line(record.dict())` writes to `data/survey.ndjson`.
  - On success → **201** with `{"status":"ok"}`.

---

## JSON Lines & Data Hygiene

- **JSON Lines** (NDJSON) is append-only and easy to parse later (pandas, Spark).
- Keep payloads small (<16KB). In Part 2, we’ll add a request-size guard and export/analytics.

---

## Troubleshooting

- **CORS/Network error**: Is `python app.py` running? Is the URL exactly `http://127.0.0.1:5000/v1/survey`?
- **Validation 422**: Read `detail` array — each item includes the field path and message.
- **Permission denied writing file**: Ensure you run from repo root so `data/` exists and is writable.

---

## Next (Part 2 teaser)

- `GET /v1/survey/export` to stream NDJSON
- Simple analytics: average rating, counts by source
- CSV export for Excel users

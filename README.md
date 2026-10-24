# bibexCV Review Assistant

Upload a text-based CV PDF, inspect/edit/redact its extracted text, select your target role and career level, optionally add a job description, then consent and click **Analyse**. No request occurs on upload or ordinary reruns. Each new Analyse click is a new request. The last successful review remains in session memory and is explicitly labelled; changing inputs does not change that review. Download it as plain text or clear the session. The synthetic demo uses fictional content and prewritten feedback, requires no credentials, and makes no API calls.

## Windows setup (PowerShell)

Install standard CPython 3.12 or 3.13 from python.org, including the Python launcher. From this directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:OPENAI_API_KEY = 'your-local-key'
$env:OPENAI_MODEL = 'gpt-4o-mini'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Alternatively put `OPENAI_API_KEY = "your-local-key"` in `.streamlit/secrets.toml` (ignored by Git). Do not paste credentials into source files. `.env` is not loaded automatically. `requirements.txt` is canonical; the old `requirement.txt` forwards to it. Model access must be checked with your own account; override OPENAI_MODEL with an accessible model supporting Chat Completions JSON output.

## Privacy and limitations

The app sends only edited CV text and role context to OpenAI after explicit consent and Analyse. Provider retention policies still apply; `store=False` is not a promise of zero provider retention. No CV/review files, database records, shared Streamlit caches, or app logs are created. SDK/transport debug logging is suppressed. Session memory lasts until cleared/session termination. Uploaded PDFs are held by Streamlit in memory; clearing resets the uploader. Downloaded feedback is sensitive and remains wherever you save it.

Maximum PDF size: 5 MB; 30 pages; extracted/edited CV: 24,000 characters; job description: 12,000 characters. Encrypted, unreadable, and image-only PDFs are rejected; use local OCR for scans. Mixed image/text PDFs may have missing content: inspect the preview. Text extraction does not assess visual layout. Quotations are checked against the submitted CV with whitespace normalisation; the entire response is rejected if a quote is absent. This validates quotations, not every AI judgement. The prompt prohibits invented achievements and ATS guarantees. Add suggested evidence only if true.

Requests time out after 30 seconds with automatic retries disabled. Errors are sanitised. A timed-out request may still be processed/billed by the provider. No request is automatically repeated. CORS/XSRF protection stays enabled; usage telemetry is disabled. The dev container installs canonical requirements and no longer disables protections.

## Offline verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app.py review.py tests
.\.venv\Scripts\python.exe -m pip check
```

Unit tests use synthetic CV text and mocked API/parser calls; integration tests generate real synthetic PDFs and use Streamlit AppTest when dependencies are installed. No tests spend API credits. See COMPLETION_REPORT.md for actual results and outstanding checks.

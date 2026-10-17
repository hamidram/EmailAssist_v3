# EmailAssist

EmailAssist turns the workflow prototyped in `notebooks/EmailAssist_v3.ipynb`
into a command-line Python project. It filters emails using the Yesterbox
approach, classifies messages, checks extracted links when Google Safe Browsing
is configured, and generates an executive summary, critical-email next steps,
reply drafts, and draft evaluations.

## Project layout

```text
EmailAssist_v3/
├── data/                    # Local email datasets (not committed)
├── notebooks/               # Original exploratory notebook
├── outputs/                 # Generated CSV and Markdown report (not committed)
├── src/
│   ├── email_assist/        # Installable application package
│   │   ├── cli.py           # Command-line entry point and file output
│   │   ├── config.py        # Environment-based configuration
│   │   ├── constants.py     # Categories and model prompts
│   │   ├── llm_client.py    # OpenAI-compatible client and JSON parsing
│   │   ├── parser.py        # CSV validation, dates, and Yesterbox filtering
│   │   ├── pipeline.py      # Triage, summaries, drafts, and usage tracking
│   │   ├── reporting.py     # Executive dashboard and Markdown report
│   │   ├── safety.py        # URL extraction and Safe Browsing integration
│   │   └── utils.py         # Shared cost calculation
│   └── *.py                 # Compatibility imports for the original scaffold
├── tests/                   # Offline unit and pipeline tests
├── .env.example             # Environment variable template
├── pyproject.toml           # Package metadata and tooling configuration
└── requirements.txt         # Editable install shortcut
```

## Setup

Requires Python 3.10 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. `OPENAI_BASE_URL` is optional and supports
OpenAI-compatible providers. `EMAIL_ASSIST_MODEL` defaults to `gpt-4o-mini`.
Estimated input/output costs default to the notebook's example rates; configure
`EMAIL_ASSIST_INPUT_COST_PER_MILLION` and
`EMAIL_ASSIST_OUTPUT_COST_PER_MILLION` for the rates applicable to your provider.

Google Safe Browsing is optional. Set `GOOGLE_SAFE_BROWSING_API_KEY` to enable
URL checks. Without it, the report explicitly marks link checking as
`not_configured`; links are not assumed safe.

## Run

By default, the command reads `data/Alex_emails_march_04.csv`, selects the
calendar day before today, and writes `outputs/processed_emails.csv`,
`outputs/email_assist_report.md`, and
`outputs/category_probability_distribution.png`. The report embeds the
category probability chart, which shows the distribution for each category
across the processed emails.

```powershell
email-assist --input data/Alex_emails_march_04.csv --as-of 2025-03-04
```

The above selects emails received on 2025-03-03. To process all rows instead:

```powershell
email-assist --input data/Alex_emails_march_04.csv --all-emails
```

Use `--output-dir` to choose another destination. The CSV preserves the source
email fields and adds the categorization, link-safety, generated response,
evaluation, token, and estimated-cost fields.
Progress bars track email categorization and critical-reply drafting without
printing per-step status text during the run.

## Tests

The test suite uses fake model and URL-check clients; it does not make network
requests or require API credentials.

```powershell
python -m pytest
```

## Data and credentials

Email contents are sent to the configured language-model provider. When enabled,
extracted URLs are sent to Google Safe Browsing. Review your providers' privacy
terms before processing real correspondence. Keep `.env`, local datasets, and
generated reports out of version control.

The previous `config/config.json` contained live-looking credentials. Those
values have been removed from the working copy. If they were real, revoke and
rotate them with their providers; use environment variables instead.

# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the single entry point: it loads environment settings, prompts the browser-use agent, normalizes bus data, and manages MongoDB + JSON writes. Dependencies live in `requirements.txt`, while contributor-facing context stays in `README.md`. Runtime artifacts (`bus_results.json`, `.env`) should remain untracked and reside alongside the script for easy inspection.

## Build, Test, and Development Commands
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # install browser-use, pymongo, playwright, dotenv
python main.py --from Mumbai --to Goa    # run a scrape (set env vars first)
python -m pytest tests/                  # execute unit tests when present
```
Run MongoDB locally (`mongodb://localhost:27017`) or export `MONGO_URI` before invoking the script; Playwright browsers will launch automatically via browser-use.

## Coding Style & Naming Conventions
Target Python 3.10+, PEP 8 formatting, and 4-space indentation. Keep functions snake_case and prefer concise docstrings like those already on `extract_json_array_from_text` and `parse_date_option`. Use type hints for new helpers and guard third-party calls with clear error messages so the CLI output remains actionable.

## Testing Guidelines
Adopt `pytest` and place suites under `tests/`, mirroring the module being exercised (e.g., `tests/test_parsers.py`). Favor deterministic unit tests for helpers that sanitize ratings, parse dates, or serialize JSON; mock external services (ChatOpenAI, MongoClient) to keep runs offline. Strive for coverage on new logic and include regression tests whenever scraping behavior changes.

## Commit & Pull Request Guidelines
Commits follow short, imperative summaries (`update README`, `add Mongo insert`). Keep related changes together and mention the feature or fix up front. PRs should describe the scenario, list reproducible steps (commands, env vars), attach sample JSON or console excerpts, and link issues when applicable.

## Security & Configuration Tips
Never commit `.env` files or API keys—load them via `python-dotenv` and document required variables (MONGO_URI, DB_NAME, COLLECTION_NAME, OPENAI_API_KEY). Validate contributor configs with `RESULT_JSON_PATH` pointing to local paths, and scrub logs before sharing since agent transcripts can expose real itineraries.

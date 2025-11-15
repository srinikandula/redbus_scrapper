# redbus-scraper-mongo

A Python utility that uses **browser-use** (LLM-driven browser automation) to scrape bus listings from [redbus.in](https://www.redbus.in), normalize the results, and save them to **MongoDB**.  
It also writes a JSON file `bus_results.json` with clean data.

---

## Features

- Automates RedBus search (source, destination, date).
- Extracts every visible bus entry with fields:
  - `bus_name`
  - `fare`
  - `rating`
- Normalizes ratings → `float` or `null`.
- Adds a timezone-aware `scraped_at` timestamp.
- Inserts documents into MongoDB.
- Exports results into `bus_results.json` with ISO timestamps and stringified `_id`.

---

## Prerequisites

- Python **3.10+**
- Running **MongoDB** instance
- API key(s) for `browser-use` / `ChatOpenAI` if required by your environment

---

## Installation

```bash
# Clone repo and create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Example .env

# MongoDB connection
```bash
MONGO_URI=mongodb://localhost:27017
DB_NAME=redbus_db
COLLECTION_NAME=bus_results
OPENAI_API_KEY=your_openai_key_here
```
## Usage

Run the scraper with:

```bash
python main.py --from Mumbai --to Hyderabad

```

> It will:

> Open redbus.in

> Fill From, To, and Date fields.

> Extract all bus entries after the page finishes loading.

> Insert results into MongoDB.

> Write bus_results.json.

## CLI Parameters

## You can parameterize source, destination, and date using CLI flags

```bash
python redbus_mongo.py --from Hyderabad --to Chennai --date today
```

- --from / -s → Source city (default: Hyderabad)

- --to / -d → Destination city (default: Chennai)

- --date / -D → Journey date (YYYY-MM-DD or today / tomorrow)

## Example Output (bus_results.json)

```json
[
  {
    "bus_name": "zingbus Maxx",
    "fare": "₹1,199 Onwards",
    "rating": 4.9,
    "scraped_at": "2025-09-23T12:34:56+00:00",
    "_id": "6567e7a6e8b4c0c1e9f0e7d2"
  }
]
```

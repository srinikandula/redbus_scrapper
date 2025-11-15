#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from dotenv import load_dotenv
from browser_use import Agent, ChatOpenAI
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "redbus_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "bus_results")
IDLE_TIMEOUT = int(os.getenv("BROWSER_USE_IDLE_TIMEOUT", "10"))
MODEL = os.getenv("MODEL", "gpt-4.1-mini")
RESULT_JSON_PATH = os.getenv("RESULT_JSON_PATH", "bus_results.json")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def extract_json_array_from_text(text: str) -> Optional[str]:
    """Try to find a JSON array in the AI output. Returns substring or None."""
    if not text:
        return None
    # Prefer fenced ```json blocks
    m = re.search(r"```(?:json)?\s*(\[\s*[\s\S]*?\])\s*```", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    # Fallback: first [ ... ] pair
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return None


def safe_parse_rating(r):
    """Return float or None for messy rating inputs."""
    if r is None:
        return None
    if isinstance(r, (int, float)):
        return float(r)
    s = str(r).strip()
    if s.lower() in ("null", "none", ""):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None


def parse_date_option(date_arg: str) -> str:
    """
    Accepts: 'today' (default), 'tomorrow', or 'YYYY-MM-DD'.
    Returns human-friendly instruction used in the LLM task (e.g. "today", "tomorrow", or '25-Sep-2025').
    """
    if not date_arg or date_arg.lower() == "today":
        return "today"
    if date_arg.lower() == "tomorrow":
        return "tomorrow"
    # try parse explicit YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(date_arg)
        # format like 25-Sep-2025 (many earlier tasks used this format)
        return dt.strftime("%d-%b-%Y")
    except Exception:
        # fallback: return raw string
        return date_arg


async def run_browser_use(source: str, dest: str, date_arg: str):
    llm = ChatOpenAI(model=MODEL)

    # craft the task using CLI values
    date_text = parse_date_option(date_arg)
    task = f"""
    Go to https://www.redbus.in (UI matches redbus.com).
    - Step 1: Click the FROM input (placeholder 'FROM', id `src`), clear it, then type exactly: {source}.
      Wait for the auto-complete list, select the suggestion whose label matches {source} (case-insensitive), then read the input value and ensure it equals {source}. 
      If it does not, reopen the autocomplete list and reselect until it matches. 
    - Click on the selected suggestion and wait for the input value to update to {source}. 
    - Please make sure the input value is exactly {source} before proceeding else restart the process from step 1.
    - Step 2: Repeat the above steps for the TO input (placeholder 'TO', id `dest`) with city: {dest}, again confirming the input value equals {dest} after selection. Click on the selected suggestion.
    - Step 3: Open the onward date picker and select {date_text}. Confirm the date badge reflects the correct text before continuing.
    - Step 4: Click the search button to load results and wait for the bus tiles/list to finish rendering.
    - Step 5: If there is a popup on the page with some text like "Select your preferred boarding point, click on the "Proceed/Continue" button to close the popup.
    - Step 6: Once results load, move to the right-hand results pane and scroll down in roughly two-screen/page increments with one second delay 
      between each scroll, repeating until the "End of list" text is visible so every bus card loads before extraction.
    - Step 7: Extract every bus in the list with fields: bus_name, fare, rating.
    - Step 8: Return ONLY a JSON array (no commentary). Each element must be an object with keys: bus_name, fare, rating.
    """

    print("Running agent with task:")
    print(task)

    agent = Agent(task=task, llm=llm, idle_timeout=IDLE_TIMEOUT)

    # run
    result = await agent.run()

    # result.final_result may be a method or a value; handle both
    raw_output = None
    if hasattr(result, "final_result"):
        final = getattr(result, "final_result")
        raw_output = final() if callable(final) else final
    else:
        raw_output = str(result)

    if not raw_output:
        print(" No final_result content available from agent.")
        return

    raw_text = str(raw_output)
    print("Raw AI output (first 400 chars):\n", raw_text[:400])

    # extract JSON substring
    json_sub = extract_json_array_from_text(raw_text)
    if not json_sub:
        print(" Could not find JSON array inside agent output. Full output:\n")
        print(raw_text)
        return

    try:
        buses = json.loads(json_sub)
    except Exception as e:
        print("JSON parsing failed:", e)
        print("Extracted JSON substring (truncated):\n", json_sub[:1000])
        return

    if not isinstance(buses, list):
        print("Parsed JSON is not a list. Type:", type(buses))
        return

    print(f"Parsed {len(buses)} bus entries")

    # normalize & add timezone-aware scraped_at (UTC)
    now_dt = datetime.now(timezone.utc)
    for b in buses:
        if not isinstance(b, dict):
            continue
        b["rating"] = safe_parse_rating(b.get("rating"))
        b["scraped_at"] = now_dt
        b["source"] = source
        b["dest"] = dest
        b["journey_date"] = date_text

    inserted_ids = None
    if buses:
        try:
            res = collection.insert_many(buses)
            inserted_ids = res.inserted_ids
            print(f"Inserted {len(inserted_ids)} docs into MongoDB '{DB_NAME}.{COLLECTION_NAME}'")
        except Exception as e:
            print("Mongo insert_many failed:", e)

    serializable = []
    for i, b in enumerate(buses):
        b_copy = dict(b)
        dt = b_copy.get("scraped_at")
        if isinstance(dt, datetime):
            b_copy["scraped_at"] = dt.isoformat()
        if inserted_ids and i < len(inserted_ids):
            try:
                b_copy["_id"] = str(inserted_ids[i])
            except Exception:
                pass
        else:
            if "_id" in b_copy:
                try:
                    b_copy["_id"] = str(b_copy["_id"])
                except Exception:
                    pass
        serializable.append(b_copy)

    with open(RESULT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False, default=str)

    print(f"Wrote results to {RESULT_JSON_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Scrape redbus and save results to MongoDB")
    parser.add_argument("--from", dest="source", required=True, help="Source city (e.g. Hyderabad)")
    parser.add_argument("--to", dest="dest", required=True, help="Destination city (e.g. Chennai)")
    parser.add_argument(
        "--date",
        dest="date",
        default="today",
        help="Date to select: 'today' (default), 'tomorrow', or YYYY-MM-DD",
    )
    args = parser.parse_args()

    asyncio.run(run_browser_use(args.source, args.dest, args.date))


if __name__ == "__main__":
    main()

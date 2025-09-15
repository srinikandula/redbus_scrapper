import asyncio
import argparse
from playwright.async_api import async_playwright

RED_BUS_URL = "https://www.redbus.in/"

# -----------------------
# City selection function
# -----------------------
async def pick_city(page, label_text: str, city: str):
    """
    Pick a city in Redbus reliably by typing and selecting the first suggestion.
    """
    # Click the input field
    button = page.locator(f"div[role='button'] .label___d74dcc:text('{label_text}')").first
    await button.click()

    # Locate input inside popup
    textbox = page.locator("div[role='dialog'] input, div[role='dialog'] [contenteditable='true']").first
    await textbox.wait_for(state="visible", timeout=10000)

    # Clear and type city
    await textbox.fill("")
    await textbox.type(city, delay=60)

    # Wait a short moment for suggestions to populate
    await page.wait_for_timeout(1000)  # 1 second

    # Click the first suggestion
    option = page.locator("[role='listbox'] [role='option']").first
    await option.click()

# -----------------------
# Main scraper function
# -----------------------
async def scrape_redbus(source: str, destination: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()
        await page.goto(RED_BUS_URL)

        # Select source & destination
        await pick_city(page, "From", source)
        await pick_city(page, "To", destination)

        # Click Search Buses
        search_btn = page.locator("button", has_text="Search Buses")
        await search_btn.click()

        # Wait for at least one bus row to appear
        # Wait for the main results container
        await page.wait_for_selector("div[id='search_results']", timeout=30000)

        # Locate all bus rows inside that container
        bus_rows = await page.locator("div[id='search_results'] div[class*='travels']").all()

        results = []
        for bus in bus_rows[:10]:
            try:
                name = await bus.locator("div[class*='travels']").inner_text()
                depart = await bus.locator("div[class*='dp-time']").inner_text()
                arrive = await bus.locator("div[class*='bp-time']").inner_text()
                price = await bus.locator("div[class*='seat-fare']").inner_text()
                results.append({
                    "name": name.strip(),
                    "depart": depart.strip(),
                    "arrive": arrive.strip(),
                    "price": price.strip()
                })
            except:
                continue

        print(f"\nBuses from {source} to {destination}:\n")
        for r in results:
            print(r)

        await browser.close()

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redbus Scraper")
    parser.add_argument("--from", dest="source", required=True, help="Source city")
    parser.add_argument("--to", dest="destination", required=True, help="Destination city")
    args = parser.parse_args()

    asyncio.run(scrape_redbus(args.source, args.destination))

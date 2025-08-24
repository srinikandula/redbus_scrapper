import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv

RED_BUS_URL = "https://www.redbus.in/"

# -----------------------
# City selection function
# -----------------------
async def pick_city(page, label_text: str, city: str):
    """
    Pick a city in Redbus reliably by typing and selecting the first suggestion.
    """
    button = page.locator(f"div[role='button'] .label___d74dcc:text('{label_text}')").first
    await button.click()

    textbox = page.locator("div[role='dialog'] input, div[role='dialog'] [contenteditable='true']").first
    await textbox.wait_for(state="visible", timeout=10000)

    await textbox.fill("")
    await textbox.type(city, delay=60)
    await page.wait_for_timeout(1000)

    option = page.locator("[role='listbox'] [role='option']").first
    await option.click()

# -----------------------
# Scrape bus details
# -----------------------
async def scrape_buses(page):
    """Scrapes all bus details from the results page using BeautifulSoup."""
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    buses = []
    for bus_li in soup.select("li.tupleWrapper___04f2bd"):
        bus = {}
        try:
            bus['name'] = bus_li.select_one(".travelsName___854b5a").text.strip()
            bus['type'] = bus_li.select_one(".busType___87f844").text.strip()
            bus['departure'] = bus_li.select_one(".boardingTime___ca56c9").text.strip()
            bus['arrival'] = bus_li.select_one(".droppingTime___70b12b").text.strip()
            bus['duration'] = bus_li.select_one(".duration___916eff").text.strip()
            bus['total_seats'] = bus_li.select_one(".totalSeats___7f6310").text.strip()

            single_seats_tag = bus_li.select_one(".singleSeats___63f11c")
            bus['single_seats'] = single_seats_tag.text.strip() if single_seats_tag else None

            bus['price'] = bus_li.select_one(".finalFare___4bd28c").text.strip()

            rating_tag = bus_li.select_one(".rating___b0d40f")
            bus['rating'] = rating_tag.text.strip() if rating_tag else None

            buses.append(bus)
        except:
            continue
    return buses

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

        # Click Search button (skip date selection)
        search_btn = page.locator("button", has_text="Search Buses")
        await search_btn.click()

        # Wait for bus list to load
        await page.wait_for_selector("li.tupleWrapper___04f2bd", timeout=20000)

        # Scrape all buses
        buses = await scrape_buses(page)

        # Print top 10 results
        print(f"\nTop 10 buses from {source} to {destination}:\n")
        for b in buses[:10]:
            print(b)

        # Save all results to CSV
        if buses:
            keys = buses[0].keys()
            with open("buses.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(buses)
            print(f"\nSaved {len(buses)} buses to buses.csv")

        await browser.close()

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    asyncio.run(scrape_redbus("Bangalore", "Hyderabad"))

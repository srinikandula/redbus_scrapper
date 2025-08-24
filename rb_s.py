import asyncio
from playwright.async_api import async_playwright, Page
from datetime import datetime




RED_BUS_URL = "https://www.redbus.in/"

async def pick_city(page, label_text: str, city: str):
    # Find the correct city field (avoids the swap button)
    button = page.locator(
        f"div[role='button'] .label___d74dcc:text('{label_text}')"
    ).first
    await button.click()

    # Locate the input inside the popup/dialog
    textbox = page.locator(
        "div[role='dialog'] input, div[role='dialog'] [contenteditable='true']"
    ).first
    await textbox.wait_for(state="visible", timeout=10000)

    # Clear old text if any
    try:
        await textbox.fill("")
    except:
        pass

    # Type city name
    await textbox.type(city, delay=60)

    # Pick first suggestion
    try:
        option = page.locator("[role='listbox'] [role='option']").first
        await option.wait_for(state="visible", timeout=5000)
        await option.click()
    except:
        li = page.locator("div[role='dialog'] li").first
        await li.wait_for(state="visible", timeout=5000)
        await li.click()


async def pick_date(page: Page, date_input: str | datetime):
    """
    Pick a date on Redbus calendar reliably.
    date_input: "YYYY-MM-DD" or datetime object
    """

    # Convert to datetime object
    if isinstance(date_input, str):
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        raise TypeError("date_input must be str or datetime")

    target_day_str = date_obj.strftime("%d %b, %Y")  # e.g., "24 Aug, 2025"

    # Click the calendar input
    calendar_div = page.locator("div.dateInputWrapper___cb5c9c").first
    await calendar_div.click(force=True)

    # Wait for the calendar popup to appear
    popup = page.locator("div[role='dialog']").first
    await popup.wait_for(state="visible", timeout=5000)

    # Check if target is Today/Tomorrow buttons
    try:
        btn = popup.locator(f"button:has-text('{target_day_str}')").first
        if await btn.is_visible():
            await btn.click()
            return
    except:
        pass  # Not Today/Tomorrow, continue

    # Otherwise, use the calendar grid
    # Each day should have aria-label like "24 August 2025"
    aria_label = date_obj.strftime("%d %B %Y")  # e.g., "24 August 2025"
    day_cell = popup.locator(f"[aria-label='{aria_label}']").first
    await day_cell.wait_for(state="visible", timeout=5000)
    await day_cell.click()


async def scrape_redbus(source: str, destination: str, date: str = "24 Aug, 2025"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()
        await page.goto(RED_BUS_URL)

        # Select source & destination
        await pick_city(page, "From", source)
        await pick_city(page, "To", destination)

        # Select date
        # await pick_date(page, "2025-08-24")

        # Click search
        search_btn = page.locator("button", has_text="Search Buses")
        await search_btn.click()

        # Wait for bus list
        await page.wait_for_selector(".bus-items", timeout=20000)

        buses = await page.locator(".bus-items").all()

        results = []
        for bus in buses[:10]:  # just first 10
            try:
                name = await bus.locator(".travels").inner_text()
                depart = await bus.locator(".dp-time").inner_text()
                arrive = await bus.locator(".bp-time").inner_text()
                price = await bus.locator(".fare .seat-fare").inner_text()
                results.append({"name": name, "depart": depart, "arrive": arrive, "price": price})
            except:
                continue

        print("Scraped results:")
        for r in results:
            print(r)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_redbus("Hyderabad", "Bangalore"))

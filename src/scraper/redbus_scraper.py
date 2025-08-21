import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from fake_useragent import UserAgent
import pandas as pd

class RedBusScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.ua = UserAgent()
        self.base_url = "https://www.redbus.in"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def initialize_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await self.browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    async def search_buses(self, source: str, destination: str, journey_date: str = None) -> str:
        if not journey_date:
            journey_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            await self.page.goto(self.base_url, wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 4))

            await self.page.fill('input[id="src"]', source)
            await asyncio.sleep(random.uniform(1, 2))
            
            await self.page.click('ul[class*="sc-dnqmqq"] li:first-child')
            await asyncio.sleep(random.uniform(1, 2))

            await self.page.fill('input[id="dest"]', destination)
            await asyncio.sleep(random.uniform(1, 2))
            
            await self.page.click('ul[class*="sc-dnqmqq"] li:first-child')
            await asyncio.sleep(random.uniform(1, 2))

            date_input = self.page.locator('input[id="onward_cal"]')
            await date_input.click()
            await asyncio.sleep(1)
            
            formatted_date = datetime.strptime(journey_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            await date_input.fill(formatted_date)
            await asyncio.sleep(1)

            search_button = self.page.locator('button[id="search_button"]')
            await search_button.click()
            
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(random.uniform(3, 5))
            
            current_url = self.page.url
            self.logger.info(f"Navigated to search results: {current_url}")
            return current_url
            
        except Exception as e:
            self.logger.error(f"Error during bus search: {str(e)}")
            raise

    async def get_bus_listings(self) -> List[Dict]:
        bus_listings = []
        
        try:
            await self.page.wait_for_selector('.bus-item', timeout=10000)
            
            bus_items = await self.page.query_selector_all('.bus-item')
            self.logger.info(f"Found {len(bus_items)} bus listings")
            
            for i, bus_item in enumerate(bus_items):
                try:
                    bus_data = await self.extract_bus_basic_info(bus_item)
                    bus_data['listing_index'] = i
                    bus_listings.append(bus_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting bus {i}: {str(e)}")
                    continue
                    
            return bus_listings
            
        except Exception as e:
            self.logger.error(f"Error getting bus listings: {str(e)}")
            return []

    async def extract_bus_basic_info(self, bus_item) -> Dict:
        bus_data = {}
        
        try:
            bus_name = await bus_item.query_selector('.travels')
            bus_data['operator_name'] = await bus_name.inner_text() if bus_name else 'N/A'
            
            bus_type = await bus_item.query_selector('.bus-type')
            bus_data['bus_type'] = await bus_type.inner_text() if bus_type else 'N/A'
            
            departure_time = await bus_item.query_selector('.dp-time')
            bus_data['departure_time'] = await departure_time.inner_text() if departure_time else 'N/A'
            
            duration = await bus_item.query_selector('.dur')
            bus_data['duration'] = await duration.inner_text() if duration else 'N/A'
            
            arrival_time = await bus_item.query_selector('.bp-time')
            bus_data['arrival_time'] = await arrival_time.inner_text() if arrival_time else 'N/A'
            
            rating = await bus_item.query_selector('.rating')
            bus_data['rating'] = await rating.inner_text() if rating else 'N/A'
            
            starting_price = await bus_item.query_selector('.fare')
            bus_data['starting_price'] = await starting_price.inner_text() if starting_price else 'N/A'
            
            seats_available = await bus_item.query_selector('.seat-left')
            bus_data['seats_available'] = await seats_available.inner_text() if seats_available else 'N/A'
            
        except Exception as e:
            self.logger.warning(f"Error extracting basic bus info: {str(e)}")
            
        return bus_data

    async def get_detailed_fare_info(self, bus_index: int) -> List[Dict]:
        try:
            bus_items = await self.page.query_selector_all('.bus-item')
            
            if bus_index >= len(bus_items):
                self.logger.warning(f"Bus index {bus_index} out of range")
                return []
            
            view_seats_button = await bus_items[bus_index].query_selector('.button')
            if not view_seats_button:
                self.logger.warning(f"View seats button not found for bus {bus_index}")
                return []
            
            await view_seats_button.click()
            await asyncio.sleep(random.uniform(2, 4))
            
            await self.page.wait_for_selector('.seat-map-container', timeout=10000)
            
            fare_details = await self.extract_seat_fare_details()
            
            close_button = await self.page.query_selector('.close-canvas')
            if close_button:
                await close_button.click()
                await asyncio.sleep(1)
            
            return fare_details
            
        except Exception as e:
            self.logger.error(f"Error getting detailed fare info for bus {bus_index}: {str(e)}")
            return []

    async def extract_seat_fare_details(self) -> List[Dict]:
        fare_details = []
        
        try:
            seat_types = await self.page.query_selector_all('.seat-type-fare')
            
            for seat_type in seat_types:
                fare_info = {}
                
                seat_category = await seat_type.query_selector('.seat-type')
                fare_info['seat_category'] = await seat_category.inner_text() if seat_category else 'N/A'
                
                fare_amount = await seat_type.query_selector('.fare-details')
                fare_info['fare'] = await fare_amount.inner_text() if fare_amount else 'N/A'
                
                available_seats = await seat_type.query_selector('.available-seats')
                fare_info['available_seats'] = await available_seats.inner_text() if available_seats else 'N/A'
                
                fare_details.append(fare_info)
                
            if not fare_details:
                seats = await self.page.query_selector_all('.seat')
                for seat in seats[:10]:
                    seat_info = {}
                    seat_class = await seat.get_attribute('class')
                    seat_info['seat_type'] = 'available' if 'available' in seat_class else 'booked'
                    
                    tooltip = await seat.get_attribute('title')
                    if tooltip and 'Rs' in tooltip:
                        fare_info['fare'] = tooltip
                    
                    fare_details.append(seat_info)
                    
        except Exception as e:
            self.logger.error(f"Error extracting seat fare details: {str(e)}")
            
        return fare_details

    async def scrape_route(self, source: str, destination: str, journey_date: str = None) -> Dict:
        scrape_results = {
            'route': f"{source} to {destination}",
            'journey_date': journey_date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            'scraped_at': datetime.now().isoformat(),
            'buses': []
        }
        
        try:
            await self.search_buses(source, destination, journey_date)
            bus_listings = await self.get_bus_listings()
            
            for i, bus_basic_info in enumerate(bus_listings):
                self.logger.info(f"Processing bus {i+1}/{len(bus_listings)}: {bus_basic_info.get('operator_name', 'Unknown')}")
                
                fare_details = await self.get_detailed_fare_info(i)
                
                bus_complete_info = {
                    **bus_basic_info,
                    'detailed_fares': fare_details,
                    'scraped_at': datetime.now().isoformat()
                }
                
                scrape_results['buses'].append(bus_complete_info)
                
                await asyncio.sleep(random.uniform(1, 3))
                
        except Exception as e:
            self.logger.error(f"Error scraping route {source} to {destination}: {str(e)}")
            
        return scrape_results

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.logger.info("Browser closed successfully")
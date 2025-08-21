#!/usr/bin/env python3
import asyncio
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from src.scraper.redbus_scraper import RedBusScraper
from src.database.data_manager import DataManager

def setup_logging():
    """Setup logging configuration"""
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/main.log'),
            logging.StreamHandler()
        ]
    )

async def scrape_single_route(source: str, destination: str, journey_date: str = None,
                             headless: bool = True) -> Dict:
    """Scrape a single route and return results"""
    logger = logging.getLogger(__name__)
    
    scraper = RedBusScraper(headless=headless)
    data_manager = DataManager()
    
    try:
        logger.info(f"Starting scrape for {source} to {destination} for date {journey_date}" )
        
        await scraper.initialize_browser()
        scrape_results = await scraper.scrape_route(source, destination, journey_date)
        
        logger.info(f"Scraping completed. Found {len(scrape_results['buses'])} buses")
        
        if scrape_results['buses']:
            storage_stats = data_manager.process_scraping_results(scrape_results)
            logger.info(f"Storage stats: {storage_stats}")
            
            return {
                'success': True,
                'scrape_results': scrape_results,
                'storage_stats': storage_stats
            }
        else:
            logger.warning("No buses found for this route")
            return {
                'success': False,
                'error': 'No buses found'
            }
            
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await scraper.close()

async def scrape_multiple_routes(routes_config: List[Dict], headless: bool = True) -> Dict:
    """Scrape multiple routes from configuration"""
    logger = logging.getLogger(__name__)
    results = {}
    
    for i, route in enumerate(routes_config):
        logger.info(f"Processing route {i+1}/{len(routes_config)}: {route}")
        
        try:
            result = await scrape_single_route(
                source=route['source'],
                destination=route['destination'],
                journey_date=route.get('journey_date'),
                headless=headless
            )
            
            route_key = f"{route['source']}_to_{route['destination']}"
            results[route_key] = result
            
            logger.info(f"Completed route {i+1}/{len(routes_config)}")
            
            if i < len(routes_config) - 1:
                logger.info("Waiting 30 seconds before next route...")
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Error processing route {route}: {str(e)}")
            results[f"{route['source']}_to_{route['destination']}"] = {
                'success': False,
                'error': str(e)
            }
    
    return results

def analyze_route_data(source: str, destination: str, days_back: int = 30):
    """Analyze route data and generate insights"""
    data_manager = DataManager()
    logger = logging.getLogger(__name__)
    
    try:
        analytics = data_manager.get_route_analytics(source, destination, days_back)
        
        print(f"\n=== Route Analytics: {analytics['route']} ===")
        print(f"Total Records: {analytics['total_records']}")
        
        if analytics['demand_analysis']:
            demand = analytics['demand_analysis']
            print(f"Average Fare: ₹{demand.get('avg_fare', 0):.2f}")
            print(f"Price Range: ₹{demand.get('min_fare', 0):.2f} - ₹{demand.get('max_fare', 0):.2f}")
            print(f"Average Available Seats: {demand.get('avg_available_seats', 0):.1f}")
        
        if analytics['price_trends']:
            trends = analytics['price_trends']
            print(f"Price Trend: {trends['trend_direction']} ({trends['trend_percentage']:+.2f}%)")
        
        if analytics['recent_fares']:
            print(f"\nRecent Fares (Top 5):")
            for i, fare in enumerate(analytics['recent_fares'][:5]):
                print(f"  {i+1}. {fare['operator_name']} - {fare['seat_category']}: ₹{fare['fare']}")
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error analyzing route data: {str(e)}")
        return None

def export_data(source: str = None, destination: str = None, output_file: str = None):
    """Export route data to CSV"""
    data_manager = DataManager()
    logger = logging.getLogger(__name__)
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if source and destination:
            output_file = f"data/export_{source}_{destination}_{timestamp}.csv"
        else:
            output_file = f"data/export_all_routes_{timestamp}.csv"
    
    try:
        Path("data").mkdir(exist_ok=True)
        records_exported = data_manager.export_route_data(source, destination, output_file)
        print(f"Exported {records_exported} records to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return None

def list_routes():
    """List all routes in the database"""
    data_manager = DataManager()
    logger = logging.getLogger(__name__)
    
    try:
        routes = data_manager.get_all_routes()
        
        if routes:
            print("\n=== Available Routes in Database ===")
            for route in routes:
                print(f"{route['source']} → {route['destination']} ({route['total_records']} records)")
        else:
            print("No routes found in database.")
        
        return routes
        
    except Exception as e:
        logger.error(f"Error listing routes: {str(e)}")
        return []

async def main():
    parser = argparse.ArgumentParser(description='RedBus Fare Scraper for Dynamic Pricing')
    
    parser.add_argument('--mode', choices=['scrape', 'analyze', 'export', 'list'], 
                       default='scrape', help='Operation mode')
    
    parser.add_argument('--source', type=str, help='Source city')
    parser.add_argument('--destination', type=str, help='Destination city')
    parser.add_argument('--date', type=str, help='Journey date (YYYY-MM-DD), default: tomorrow')
    parser.add_argument('--config', type=str, help='Path to routes configuration file')
    parser.add_argument('--headless', action='store_true', default=True, 
                       help='Run browser in headless mode')
    parser.add_argument('--days-back', type=int, default=30, 
                       help='Days back for analysis (default: 30)')
    parser.add_argument('--output', type=str, help='Output file path for export')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.mode == 'scrape':
        if args.config:
            try:
                with open(args.config, 'r') as f:
                    routes_config = json.load(f)
                
                logger.info(f"Loaded {len(routes_config)} routes from config file")
                results = await scrape_multiple_routes(routes_config, args.headless)
                
                print("\n=== Scraping Results Summary ===")
                for route_key, result in results.items():
                    status = "✓" if result['success'] else "✗"
                    print(f"{status} {route_key.replace('_', ' ')}")
                    
            except Exception as e:
                logger.error(f"Error loading config file: {str(e)}")
                
        elif args.source and args.destination:
            result = await scrape_single_route(
                source=args.source,
                destination=args.destination,
                journey_date=args.date,
                headless=args.headless
            )
            
            if result['success']:
                print(f"✓ Successfully scraped {args.source} to {args.destination}")
                if 'storage_stats' in result:
                    stats = result['storage_stats']
                    print(f"  Stored: {stats['successfully_stored']}/{stats['total_buses']} buses")
            else:
                print(f"✗ Failed to scrape {args.source} to {args.destination}: {result.get('error', 'Unknown error')}")
                
        else:
            print("For scrape mode, provide either --config file or --source and --destination")
    
    elif args.mode == 'analyze':
        if args.source and args.destination:
            analyze_route_data(args.source, args.destination, args.days_back)
        else:
            print("For analyze mode, provide --source and --destination")
    
    elif args.mode == 'export':
        export_data(args.source, args.destination, args.output)
    
    elif args.mode == 'list':
        list_routes()

if __name__ == "__main__":
    asyncio.run(main())
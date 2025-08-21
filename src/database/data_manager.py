import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from src.models.database_models import DatabaseManager
from bson import ObjectId
import re

class DataManager:
    def __init__(self, connection_string: str = "mongodb://localhost:27017", db_name: str = "redbus_fares"):
        self.db = DatabaseManager(connection_string, db_name)
        self.logger = logging.getLogger(__name__)
    
    def process_scraping_results(self, scrape_results: Dict) -> Dict:
        """Process and store scraping results in the database"""
        stats = {
            'route_processed': False,
            'total_buses': 0,
            'successfully_stored': 0,
            'errors': []
        }
        
        try:
            route_info = self._parse_route_info(scrape_results['route'])
            if not route_info:
                stats['errors'].append("Could not parse route information")
                return stats
            
            route_id = self.db.insert_route(
                source=route_info['source'],
                destination=route_info['destination']
            )
            
            session_id = self.db.start_scraping_session(
                route_id=route_id,
                journey_date=scrape_results['journey_date']
            )
            
            stats['total_buses'] = len(scrape_results['buses'])
            
            for bus_data in scrape_results['buses']:
                try:
                    success = self._store_bus_data(bus_data, route_id, scrape_results['journey_date'])
                    if success:
                        stats['successfully_stored'] += 1
                except Exception as e:
                    error_msg = f"Error storing bus data: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            self.db.update_scraping_session(
                session_id=session_id,
                total_buses=stats['total_buses'],
                successful_scrapes=stats['successfully_stored'],
                status='completed'
            )
            
            stats['route_processed'] = True
            
        except Exception as e:
            error_msg = f"Error processing scraping results: {str(e)}"
            stats['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return stats
    
    def _parse_route_info(self, route_string: str) -> Optional[Dict]:
        """Parse route string like 'Hyderabad to Bangalore' into source and destination"""
        try:
            if ' to ' in route_string:
                parts = route_string.split(' to ')
                if len(parts) == 2:
                    return {
                        'source': parts[0].strip(),
                        'destination': parts[1].strip()
                    }
        except Exception:
            pass
        return None
    
    def _store_bus_data(self, bus_data: Dict, route_id: ObjectId, journey_date: str) -> bool:
        """Store individual bus data in the database"""
        try:
            operator_name = bus_data.get('operator_name', 'Unknown')
            rating = self._extract_rating(bus_data.get('rating'))
            
            operator_id = self.db.insert_operator(
                name=operator_name,
                rating=rating
            )
            
            if not operator_id:
                return False
            
            service_id = self.db.insert_service(
                route_id=route_id,
                operator_id=operator_id,
                bus_type=bus_data.get('bus_type', 'Unknown'),
                departure_time=bus_data.get('departure_time', ''),
                arrival_time=bus_data.get('arrival_time', ''),
                duration=bus_data.get('duration', ''),
                rating=rating
            )
            
            starting_price = self._extract_price(bus_data.get('starting_price'))
            
            detailed_fares = bus_data.get('detailed_fares', [])
            if detailed_fares:
                for fare_detail in detailed_fares:
                    fare_amount = self._extract_price(fare_detail.get('fare'))
                    available_seats = self._extract_seats_count(fare_detail.get('available_seats'))
                    
                    if fare_amount and fare_amount > 0:
                        self.db.insert_fare_data(
                            service_id=service_id,
                            journey_date=journey_date,
                            seat_category=fare_detail.get('seat_category', 'Unknown'),
                            fare=fare_amount,
                            available_seats=available_seats or 0,
                            starting_price=starting_price
                        )
            else:
                if starting_price and starting_price > 0:
                    seats_available = self._extract_seats_count(bus_data.get('seats_available'))
                    self.db.insert_fare_data(
                        service_id=service_id,
                        journey_date=journey_date,
                        seat_category='Standard',
                        fare=starting_price,
                        available_seats=seats_available or 0,
                        starting_price=starting_price
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing bus data: {str(e)}")
            return False
    
    def _extract_rating(self, rating_str: str) -> Optional[float]:
        """Extract numeric rating from rating string"""
        if not rating_str or rating_str == 'N/A':
            return None
        
        try:
            rating_match = re.search(r'(\d+\.?\d*)', str(rating_str))
            if rating_match:
                rating = float(rating_match.group(1))
                return rating if 0 <= rating <= 5 else None
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _extract_price(self, price_str: str) -> Optional[float]:
        """Extract numeric price from price string"""
        if not price_str or price_str == 'N/A':
            return None
        
        try:
            price_match = re.search(r'(\d+\.?\d*)', str(price_str).replace(',', ''))
            if price_match:
                return float(price_match.group(1))
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _extract_seats_count(self, seats_str: str) -> Optional[int]:
        """Extract numeric seats count from seats string"""
        if not seats_str or seats_str == 'N/A':
            return None
        
        try:
            seats_match = re.search(r'(\d+)', str(seats_str))
            if seats_match:
                return int(seats_match.group(1))
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def get_route_analytics(self, source: str, destination: str, days_back: int = 30) -> Dict:
        """Get analytics for a specific route"""
        try:
            fare_history = self.db.get_route_fare_history(source, destination, days_back)
            demand_analysis = self.db.get_demand_analysis(source, destination)
            
            analytics = {
                'route': f"{source} to {destination}",
                'total_records': len(fare_history),
                'demand_analysis': demand_analysis,
                'recent_fares': fare_history[:10],
                'price_trends': self._calculate_price_trends(fare_history)
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting route analytics: {str(e)}")
            return {}
    
    def _calculate_price_trends(self, fare_history: List[Dict]) -> Dict:
        """Calculate price trends from fare history"""
        if not fare_history:
            return {}
        
        try:
            fares_by_date = {}
            for record in fare_history:
                date = record['journey_date']
                fare = record['fare']
                
                if date not in fares_by_date:
                    fares_by_date[date] = []
                fares_by_date[date].append(fare)
            
            avg_fares_by_date = {
                date: sum(fares) / len(fares)
                for date, fares in fares_by_date.items()
            }
            
            sorted_dates = sorted(avg_fares_by_date.keys())
            
            if len(sorted_dates) >= 2:
                recent_avg = avg_fares_by_date[sorted_dates[-1]]
                previous_avg = avg_fares_by_date[sorted_dates[-2]]
                trend_percent = ((recent_avg - previous_avg) / previous_avg) * 100
            else:
                trend_percent = 0
            
            return {
                'average_fares_by_date': avg_fares_by_date,
                'trend_percentage': round(trend_percent, 2),
                'trend_direction': 'up' if trend_percent > 0 else 'down' if trend_percent < 0 else 'stable'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating price trends: {str(e)}")
            return {}
    
    def export_route_data(self, source: str, destination: str, output_path: str) -> int:
        """Export route data to CSV"""
        try:
            return self.db.export_data_to_csv(output_path, source, destination)
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
            return 0
    
    def get_all_routes(self) -> List[Dict]:
        """Get all routes in the database"""
        try:
            pipeline = [
                {
                    "$lookup": {
                        "from": "bus_services",
                        "localField": "_id",
                        "foreignField": "route_id",
                        "as": "services"
                    }
                },
                {
                    "$lookup": {
                        "from": "fare_data",
                        "localField": "services._id",
                        "foreignField": "service_id",
                        "as": "fares"
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "source": "$source",
                            "destination": "$destination"
                        },
                        "total_records": {"$sum": {"$size": "$fares"}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "source": "$_id.source",
                        "destination": "$_id.destination",
                        "total_records": 1
                    }
                },
                {
                    "$sort": {"total_records": -1}
                }
            ]
            
            return list(self.db.db.routes.aggregate(pipeline))
                
        except Exception as e:
            self.logger.error(f"Error getting all routes: {str(e)}")
            return []
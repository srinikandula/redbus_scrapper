import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from bson import ObjectId
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

@dataclass
class Route:
    _id: Optional[ObjectId]
    source: str
    destination: str
    distance_km: Optional[float] = None
    created_at: Optional[datetime] = None

@dataclass
class BusOperator:
    _id: Optional[ObjectId]
    name: str
    rating: Optional[float] = None
    created_at: Optional[datetime] = None

@dataclass
class BusService:
    _id: Optional[ObjectId]
    route_id: ObjectId
    operator_id: ObjectId
    bus_type: str
    departure_time: str
    arrival_time: str
    duration: str
    rating: Optional[float] = None
    created_at: Optional[datetime] = None

@dataclass
class FareData:
    _id: Optional[ObjectId]
    service_id: ObjectId
    journey_date: str
    seat_category: str
    fare: float
    available_seats: int
    starting_price: Optional[float] = None
    scraped_at: Optional[datetime] = None
    demand_factor: Optional[float] = None

@dataclass
class ScrapingSession:
    _id: Optional[ObjectId]
    route_id: ObjectId
    journey_date: str
    total_buses_found: int
    successful_scrapes: int
    session_start: datetime
    session_end: Optional[datetime] = None
    status: str = 'active'

class DatabaseManager:
    def __init__(self, connection_string: str = "mongodb://localhost:27017", db_name: str = "redbus_fares"):
        self.connection_string = connection_string
        self.db_name = db_name
        self.client = None
        self.db = None
        self.init_database()
    
    def init_database(self):
        """Initialize MongoDB connection and create indexes"""
        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.db_name]
        
        # Create indexes for better performance
        self.db.routes.create_index([("source", 1), ("destination", 1)], unique=True)
        self.db.bus_operators.create_index("name", unique=True)
        self.db.fare_data.create_index("journey_date")
        self.db.fare_data.create_index("service_id")
        self.db.scraping_sessions.create_index("route_id")
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        return self.db[collection_name]
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def insert_route(self, source: str, destination: str, distance_km: float = None) -> ObjectId:
        """Insert or get existing route"""
        try:
            route_data = {
                "source": source,
                "destination": destination,
                "distance_km": distance_km,
                "created_at": datetime.utcnow()
            }
            
            result = self.db.routes.update_one(
                {"source": source, "destination": destination},
                {"$setOnInsert": route_data},
                upsert=True
            )
            
            if result.upserted_id:
                return result.upserted_id
            else:
                existing_route = self.db.routes.find_one({"source": source, "destination": destination})
                return existing_route["_id"]
                
        except Exception as e:
            print(f"Error inserting route: {e}")
            return None
    
    def insert_operator(self, name: str, rating: float = None) -> ObjectId:
        """Insert or get existing operator"""
        try:
            operator_data = {
                "name": name,
                "rating": rating,
                "created_at": datetime.utcnow()
            }
            
            result = self.db.bus_operators.update_one(
                {"name": name},
                {"$setOnInsert": operator_data},
                upsert=True
            )
            
            if result.upserted_id:
                return result.upserted_id
            else:
                existing_operator = self.db.bus_operators.find_one({"name": name})
                return existing_operator["_id"]
                
        except Exception as e:
            print(f"Error inserting operator: {e}")
            return None
    
    def insert_service(self, route_id: ObjectId, operator_id: ObjectId, bus_type: str,
                      departure_time: str, arrival_time: str, duration: str,
                      rating: float = None) -> ObjectId:
        """Insert bus service"""
        try:
            service_data = {
                "route_id": route_id,
                "operator_id": operator_id,
                "bus_type": bus_type,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": duration,
                "rating": rating,
                "created_at": datetime.utcnow()
            }
            
            result = self.db.bus_services.insert_one(service_data)
            return result.inserted_id
            
        except Exception as e:
            print(f"Error inserting service: {e}")
            return None
    
    def insert_fare_data(self, service_id: ObjectId, journey_date: str, seat_category: str,
                        fare: float, available_seats: int, starting_price: float = None) -> ObjectId:
        """Insert fare data"""
        try:
            fare_data = {
                "service_id": service_id,
                "journey_date": journey_date,
                "seat_category": seat_category,
                "fare": fare,
                "available_seats": available_seats,
                "starting_price": starting_price,
                "scraped_at": datetime.utcnow()
            }
            
            result = self.db.fare_data.insert_one(fare_data)
            return result.inserted_id
            
        except Exception as e:
            print(f"Error inserting fare data: {e}")
            return None
    
    def start_scraping_session(self, route_id: ObjectId, journey_date: str) -> ObjectId:
        """Start a new scraping session"""
        try:
            session_data = {
                "route_id": route_id,
                "journey_date": journey_date,
                "total_buses_found": 0,
                "successful_scrapes": 0,
                "session_start": datetime.utcnow(),
                "status": "active"
            }
            
            result = self.db.scraping_sessions.insert_one(session_data)
            return result.inserted_id
            
        except Exception as e:
            print(f"Error starting scraping session: {e}")
            return None
    
    def update_scraping_session(self, session_id: ObjectId, total_buses: int = None,
                               successful_scrapes: int = None, status: str = None):
        """Update scraping session"""
        try:
            update_data = {}
            
            if total_buses is not None:
                update_data["total_buses_found"] = total_buses
            
            if successful_scrapes is not None:
                update_data["successful_scrapes"] = successful_scrapes
            
            if status is not None:
                update_data["status"] = status
                
                if status == 'completed':
                    update_data["session_end"] = datetime.utcnow()
            
            if update_data:
                self.db.scraping_sessions.update_one(
                    {"_id": session_id},
                    {"$set": update_data}
                )
                
        except Exception as e:
            print(f"Error updating scraping session: {e}")
    
    def get_route_fare_history(self, source: str, destination: str, 
                              days_back: int = 30) -> List[Dict]:
        """Get fare history for a route"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            pipeline = [
                {
                    "$lookup": {
                        "from": "bus_services",
                        "localField": "service_id",
                        "foreignField": "_id",
                        "as": "service"
                    }
                },
                {"$unwind": "$service"},
                {
                    "$lookup": {
                        "from": "routes",
                        "localField": "service.route_id",
                        "foreignField": "_id",
                        "as": "route"
                    }
                },
                {"$unwind": "$route"},
                {
                    "$lookup": {
                        "from": "bus_operators",
                        "localField": "service.operator_id",
                        "foreignField": "_id",
                        "as": "operator"
                    }
                },
                {"$unwind": "$operator"},
                {
                    "$match": {
                        "route.source": source,
                        "route.destination": destination,
                        "scraped_at": {"$gte": cutoff_date}
                    }
                },
                {
                    "$sort": {"journey_date": -1, "fare": 1}
                },
                {
                    "$project": {
                        "journey_date": 1,
                        "operator_name": "$operator.name",
                        "bus_type": "$service.bus_type",
                        "seat_category": 1,
                        "fare": 1,
                        "available_seats": 1,
                        "scraped_at": 1
                    }
                }
            ]
            
            return list(self.db.fare_data.aggregate(pipeline))
            
        except Exception as e:
            print(f"Error getting route fare history: {e}")
            return []
    
    def get_demand_analysis(self, source: str, destination: str) -> Dict:
        """Get demand analysis for a route"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            pipeline = [
                {
                    "$lookup": {
                        "from": "bus_services",
                        "localField": "service_id",
                        "foreignField": "_id",
                        "as": "service"
                    }
                },
                {"$unwind": "$service"},
                {
                    "$lookup": {
                        "from": "routes",
                        "localField": "service.route_id",
                        "foreignField": "_id",
                        "as": "route"
                    }
                },
                {"$unwind": "$route"},
                {
                    "$match": {
                        "route.source": source,
                        "route.destination": destination,
                        "scraped_at": {"$gte": cutoff_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_fare": {"$avg": "$fare"},
                        "min_fare": {"$min": "$fare"},
                        "max_fare": {"$max": "$fare"},
                        "avg_available_seats": {"$avg": "$available_seats"},
                        "total_records": {"$sum": 1}
                    }
                }
            ]
            
            result = list(self.db.fare_data.aggregate(pipeline))
            if result:
                data = result[0]
                data.pop("_id", None)
                return data
            return {}
            
        except Exception as e:
            print(f"Error getting demand analysis: {e}")
            return {}
    
    def export_data_to_csv(self, output_path: str, source: str = None, destination: str = None):
        """Export data to CSV"""
        try:
            import pandas as pd
            
            match_conditions = {}
            if source and destination:
                match_conditions["route.source"] = source
                match_conditions["route.destination"] = destination
            
            pipeline = [
                {
                    "$lookup": {
                        "from": "bus_services",
                        "localField": "service_id",
                        "foreignField": "_id",
                        "as": "service"
                    }
                },
                {"$unwind": "$service"},
                {
                    "$lookup": {
                        "from": "routes",
                        "localField": "service.route_id",
                        "foreignField": "_id",
                        "as": "route"
                    }
                },
                {"$unwind": "$route"},
                {
                    "$lookup": {
                        "from": "bus_operators",
                        "localField": "service.operator_id",
                        "foreignField": "_id",
                        "as": "operator"
                    }
                },
                {"$unwind": "$operator"},
                {
                    "$project": {
                        "source": "$route.source",
                        "destination": "$route.destination",
                        "operator_name": "$operator.name",
                        "bus_type": "$service.bus_type",
                        "departure_time": "$service.departure_time",
                        "arrival_time": "$service.arrival_time",
                        "duration": "$service.duration",
                        "journey_date": 1,
                        "seat_category": 1,
                        "fare": 1,
                        "available_seats": 1,
                        "scraped_at": 1
                    }
                },
                {
                    "$sort": {"scraped_at": -1, "source": 1, "destination": 1}
                }
            ]
            
            if match_conditions:
                pipeline.insert(-1, {"$match": match_conditions})
            
            data = list(self.db.fare_data.aggregate(pipeline))
            
            if data:
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False)
                return len(df)
            else:
                return 0
                
        except Exception as e:
            print(f"Error exporting data to CSV: {e}")
            return 0
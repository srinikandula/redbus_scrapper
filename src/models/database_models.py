import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Route:
    id: Optional[int]
    source: str
    destination: str
    distance_km: Optional[float] = None
    created_at: Optional[str] = None

@dataclass
class BusOperator:
    id: Optional[int]
    name: str
    rating: Optional[float] = None
    created_at: Optional[str] = None

@dataclass
class BusService:
    id: Optional[int]
    route_id: int
    operator_id: int
    bus_type: str
    departure_time: str
    arrival_time: str
    duration: str
    rating: Optional[float] = None
    created_at: Optional[str] = None

@dataclass
class FareData:
    id: Optional[int]
    service_id: int
    journey_date: str
    seat_category: str
    fare: float
    available_seats: int
    starting_price: Optional[float] = None
    scraped_at: str = None
    demand_factor: Optional[float] = None

@dataclass
class ScrapingSession:
    id: Optional[int]
    route_id: int
    journey_date: str
    total_buses_found: int
    successful_scrapes: int
    session_start: str
    session_end: Optional[str] = None
    status: str = 'active'

class DatabaseManager:
    def __init__(self, db_path: str = "data/redbus_fares.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    distance_km REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, destination)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bus_operators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bus_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id INTEGER NOT NULL,
                    operator_id INTEGER NOT NULL,
                    bus_type TEXT NOT NULL,
                    departure_time TEXT NOT NULL,
                    arrival_time TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id),
                    FOREIGN KEY (operator_id) REFERENCES bus_operators (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fare_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id INTEGER NOT NULL,
                    journey_date DATE NOT NULL,
                    seat_category TEXT NOT NULL,
                    fare REAL NOT NULL,
                    available_seats INTEGER NOT NULL,
                    starting_price REAL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    demand_factor REAL,
                    FOREIGN KEY (service_id) REFERENCES bus_services (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id INTEGER NOT NULL,
                    journey_date DATE NOT NULL,
                    total_buses_found INTEGER DEFAULT 0,
                    successful_scrapes INTEGER DEFAULT 0,
                    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_end TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_fare_data_date ON fare_data(journey_date);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_fare_data_service ON fare_data(service_id);
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_routes_source_dest ON routes(source, destination);
            ''')
            
            conn.commit()
    
    def insert_route(self, source: str, destination: str, distance_km: float = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO routes (source, destination, distance_km)
                VALUES (?, ?, ?)
            ''', (source, destination, distance_km))
            
            cursor.execute('''
                SELECT id FROM routes WHERE source = ? AND destination = ?
            ''', (source, destination))
            
            return cursor.fetchone()[0]
    
    def insert_operator(self, name: str, rating: float = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO bus_operators (name, rating)
                VALUES (?, ?)
            ''', (name, rating))
            
            cursor.execute('''
                SELECT id FROM bus_operators WHERE name = ?
            ''', (name,))
            
            result = cursor.fetchone()
            return result[0] if result else None
    
    def insert_service(self, route_id: int, operator_id: int, bus_type: str,
                      departure_time: str, arrival_time: str, duration: str,
                      rating: float = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bus_services 
                (route_id, operator_id, bus_type, departure_time, arrival_time, duration, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (route_id, operator_id, bus_type, departure_time, arrival_time, duration, rating))
            
            return cursor.lastrowid
    
    def insert_fare_data(self, service_id: int, journey_date: str, seat_category: str,
                        fare: float, available_seats: int, starting_price: float = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO fare_data 
                (service_id, journey_date, seat_category, fare, available_seats, starting_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (service_id, journey_date, seat_category, fare, available_seats, starting_price))
            
            return cursor.lastrowid
    
    def start_scraping_session(self, route_id: int, journey_date: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_sessions (route_id, journey_date)
                VALUES (?, ?)
            ''', (route_id, journey_date))
            
            return cursor.lastrowid
    
    def update_scraping_session(self, session_id: int, total_buses: int = None,
                               successful_scrapes: int = None, status: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if total_buses is not None:
                updates.append("total_buses_found = ?")
                params.append(total_buses)
            
            if successful_scrapes is not None:
                updates.append("successful_scrapes = ?")
                params.append(successful_scrapes)
            
            if status is not None:
                updates.append("status = ?")
                params.append(status)
                
                if status == 'completed':
                    updates.append("session_end = CURRENT_TIMESTAMP")
            
            if updates:
                query = f"UPDATE scraping_sessions SET {', '.join(updates)} WHERE id = ?"
                params.append(session_id)
                cursor.execute(query, params)
    
    def get_route_fare_history(self, source: str, destination: str, 
                              days_back: int = 30) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    fd.journey_date,
                    bo.name as operator_name,
                    bs.bus_type,
                    fd.seat_category,
                    fd.fare,
                    fd.available_seats,
                    fd.scraped_at
                FROM fare_data fd
                JOIN bus_services bs ON fd.service_id = bs.id
                JOIN bus_operators bo ON bs.operator_id = bo.id
                JOIN routes r ON bs.route_id = r.id
                WHERE r.source = ? AND r.destination = ?
                AND fd.journey_date >= date('now', '-' || ? || ' days')
                ORDER BY fd.journey_date DESC, fd.fare ASC
            ''', (source, destination, days_back))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_demand_analysis(self, source: str, destination: str) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    AVG(fd.fare) as avg_fare,
                    MIN(fd.fare) as min_fare,
                    MAX(fd.fare) as max_fare,
                    AVG(fd.available_seats) as avg_available_seats,
                    COUNT(*) as total_records
                FROM fare_data fd
                JOIN bus_services bs ON fd.service_id = bs.id
                JOIN routes r ON bs.route_id = r.id
                WHERE r.source = ? AND r.destination = ?
                AND fd.journey_date >= date('now', '-30 days')
            ''', (source, destination))
            
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return {}
    
    def export_data_to_csv(self, output_path: str, source: str = None, destination: str = None):
        import pandas as pd
        
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    r.source,
                    r.destination,
                    bo.name as operator_name,
                    bs.bus_type,
                    bs.departure_time,
                    bs.arrival_time,
                    bs.duration,
                    fd.journey_date,
                    fd.seat_category,
                    fd.fare,
                    fd.available_seats,
                    fd.scraped_at
                FROM fare_data fd
                JOIN bus_services bs ON fd.service_id = bs.id
                JOIN bus_operators bo ON bs.operator_id = bo.id
                JOIN routes r ON bs.route_id = r.id
            '''
            
            params = []
            if source and destination:
                query += " WHERE r.source = ? AND r.destination = ?"
                params = [source, destination]
            
            query += " ORDER BY fd.journey_date DESC, r.source, r.destination"
            
            df = pd.read_sql_query(query, conn, params=params)
            df.to_csv(output_path, index=False)
            
            return len(df)
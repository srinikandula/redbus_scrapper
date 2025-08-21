# RedBus Scraper - MongoDB Configuration

## Project Overview
This is a RedBus fare scraper application that collects bus fare data for dynamic pricing analysis. The project has been configured to use **MongoDB** as the database backend.

## Database Setup

### MongoDB Configuration
- **Database**: MongoDB (migrated from SQLite)
- **Connection**: `mongodb://localhost:27017`
- **Database Name**: `redbus_fares`
- **Dependencies**: `pymongo==4.6.0`, `motor==3.3.2`

### Collections Structure

#### routes
```json
{
  "_id": ObjectId,
  "source": "String",
  "destination": "String", 
  "distance_km": "Number (optional)",
  "created_at": "Date"
}
```

#### bus_operators
```json
{
  "_id": ObjectId,
  "name": "String (unique)",
  "rating": "Number (optional)",
  "created_at": "Date"
}
```

#### bus_services
```json
{
  "_id": ObjectId,
  "route_id": ObjectId,
  "operator_id": ObjectId,
  "bus_type": "String",
  "departure_time": "String",
  "arrival_time": "String", 
  "duration": "String",
  "rating": "Number (optional)",
  "created_at": "Date"
}
```

#### fare_data
```json
{
  "_id": ObjectId,
  "service_id": ObjectId,
  "journey_date": "String",
  "seat_category": "String",
  "fare": "Number",
  "available_seats": "Number",
  "starting_price": "Number (optional)",
  "scraped_at": "Date",
  "demand_factor": "Number (optional)"
}
```

#### scraping_sessions
```json
{
  "_id": ObjectId,
  "route_id": ObjectId,
  "journey_date": "String",
  "total_buses_found": "Number",
  "successful_scrapes": "Number", 
  "session_start": "Date",
  "session_end": "Date (optional)",
  "status": "String"
}
```

## Installation & Setup

### 1. Install MongoDB
Make sure MongoDB is installed and running on your system:
```bash
# On macOS
brew install mongodb-community
brew services start mongodb-community

# On Ubuntu
sudo apt-get install mongodb
sudo systemctl start mongodb
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
# Scrape a single route
python main.py --mode scrape --source "Hyderabad" --destination "Bangalore"

# Analyze route data
python main.py --mode analyze --source "Hyderabad" --destination "Bangalore"

# Export data to CSV
python main.py --mode export --source "Hyderabad" --destination "Bangalore"

# List all routes
python main.py --mode list
```

## Key Features

### Data Collection
- Web scraping using Playwright
- Rate limiting and error handling
- Session tracking for scraping runs

### Data Storage  
- MongoDB with proper indexing
- Upsert operations for routes and operators
- Aggregation pipelines for analytics

### Analytics
- Route fare history analysis
- Demand analysis with price trends
- CSV export functionality

## Configuration

### MongoDB Connection
The database connection can be configured in the DataManager initialization:
```python
data_manager = DataManager(
    connection_string="mongodb://localhost:27017",
    db_name="redbus_fares" 
)
```

### Environment Variables
You can set these environment variables:
- `MONGODB_URI`: MongoDB connection string (default: mongodb://localhost:27017)
- `MONGODB_DATABASE`: Database name (default: redbus_fares)

## Development Commands

### Testing
```bash
# Test MongoDB connection
python -c "from src.models.database_models import DatabaseManager; db = DatabaseManager(); print('MongoDB connection successful')"

# Run linting (if available)
python -m flake8 src/

# Run type checking (if available)  
python -m mypy src/
```

### Debugging
- Check MongoDB logs: `tail -f /usr/local/var/log/mongodb/mongo.log`
- Use MongoDB Compass for GUI database management
- Enable debug logging in the application for detailed output

## File Structure
```
redbus_scrapper/
├── src/
│   ├── database/
│   │   └── data_manager.py          # Main data processing logic
│   ├── models/
│   │   └── database_models.py       # MongoDB models and operations
│   └── scraper/
│       └── redbus_scraper.py        # Web scraping logic
├── config/
│   └── routes.json                  # Route configurations
├── data/                            # Export files location
├── logs/                            # Application logs
├── main.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
└── CLAUDE.md                        # This documentation
```

## Migration Notes
- Migrated from SQLite to MongoDB
- Changed from integer IDs to ObjectId
- Updated all database operations to use MongoDB aggregation pipelines
- Maintained backward compatibility for data export functionality
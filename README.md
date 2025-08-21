# RedBus Fare Scraper for Dynamic Pricing

A Python project to scrape bus ticket fares from RedBus for building a dynamic pricing module. The scraper searches buses between source and destination combinations, navigates to search results, extracts seat/fare information, and builds a MongoDB database for fare analysis and dynamic pricing strategies.

## Features

- **Automated Bus Search**: Search buses between any source-destination combination
- **Detailed Fare Extraction**: Extract seat categories, prices, and availability
- **MongoDB Storage**: Store fare data in MongoDB database with proper collections and indexing
- **Analytics & Insights**: Analyze price trends and demand patterns
- **Export Functionality**: Export data to CSV for further analysis
- **Multiple Route Support**: Process multiple routes from configuration
- **Robust Error Handling**: Handle network issues and site changes gracefully

## Project Structure

```
redbus_scrapper/
├── src/
│   ├── scraper/
│   │   └── redbus_scraper.py      # Main scraping logic
│   ├── database/
│   │   └── data_manager.py        # Database operations
│   └── models/
│       └── database_models.py     # Database schema and models
├── config/
│   └── routes.json                # Route configurations
├── data/                          # Export files
├── logs/                          # Log files
├── main.py                        # Main application entry point
├── requirements.txt               # Python dependencies (legacy)
├── pyproject.toml                 # Modern Python project configuration
├── CLAUDE.md                       # MongoDB setup and configuration guide
└── README.md                      # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd redbus_scrapper
   ```

2. **Install uv (if not already installed)**:
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or using pip
   pip install uv
   ```

3. **Create virtual environment with uv**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install MongoDB**:
   ```bash
   # On macOS
   brew install mongodb-community
   brew services start mongodb-community

   # On Ubuntu
   sudo apt-get install mongodb
   sudo systemctl start mongodb
   ```

5. **Install dependencies with uv**:
   ```bash
   # Option 1: Install from requirements.txt
   uv pip install -r requirements.txt
   
   # Option 2: Install using pyproject.toml (recommended)
   uv pip install -e .
   
   # Option 3: Install with development dependencies
   uv pip install -e ".[dev]"
   ```

6. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

7. **Create necessary directories**:
   ```bash
   mkdir -p data logs
   ```

## Usage

### 1. Scrape Single Route

```bash
python main.py --mode scrape --source "Hyderabad" --destination "Bangalore"
```

### 2. Scrape Multiple Routes from Config

```bash
python main.py --mode scrape --config config/routes.json
```

### 3. Analyze Route Data

```bash
python main.py --mode analyze --source "Hyderabad" --destination "Bangalore" --days-back 30
```

### 4. Export Data to CSV

```bash
# Export specific route
python main.py --mode export --source "Hyderabad" --destination "Bangalore"

# Export all routes
python main.py --mode export
```

### 5. List Available Routes

```bash
python main.py --mode list
```

## Configuration

### Routes Configuration (config/routes.json)

Edit the `config/routes.json` file to add your desired routes:

```json
[
  {
    "source": "Hyderabad",
    "destination": "Bangalore", 
    "journey_date": null
  },
  {
    "source": "Mumbai",
    "destination": "Pune",
    "journey_date": "2024-01-15"
  }
]
```

### Environment Variables

Copy `.env.example` to `.env` and modify settings:

```env
HEADLESS_MODE=true
DELAY_BETWEEN_REQUESTS=2
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=redbus_fares
```

## Database Schema

The project uses **MongoDB** with the following main collections:

### Collections Structure

#### routes
```json
{
  "_id": "ObjectId",
  "source": "String",
  "destination": "String",
  "distance_km": "Number (optional)",
  "created_at": "Date"
}
```

#### bus_operators
```json
{
  "_id": "ObjectId",
  "name": "String (unique)",
  "rating": "Number (optional)",
  "created_at": "Date"
}
```

#### bus_services
```json
{
  "_id": "ObjectId",
  "route_id": "ObjectId",
  "operator_id": "ObjectId",
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
  "_id": "ObjectId",
  "service_id": "ObjectId",
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
  "_id": "ObjectId",
  "route_id": "ObjectId",
  "journey_date": "String",
  "total_buses_found": "Number",
  "successful_scrapes": "Number",
  "session_start": "Date",
  "session_end": "Date (optional)",
  "status": "String"
}
```

### MongoDB Features
- **Proper indexing** on frequently queried fields
- **Aggregation pipelines** for complex analytics
- **Upsert operations** for routes and operators
- **Flexible schema** for evolving requirements

## Analytics & Insights

The system provides:

- **Price Trends**: Track fare changes over time
- **Demand Analysis**: Average fares, availability patterns
- **Route Comparison**: Compare different routes and operators
- **Export Capabilities**: CSV exports for external analysis

## Dynamic Pricing Applications

The scraped data can be used for:

1. **Competitive Analysis**: Monitor competitor pricing
2. **Demand Forecasting**: Predict high-demand periods
3. **Price Optimization**: Set optimal prices based on market data
4. **Route Performance**: Analyze profitable routes
5. **Seasonal Trends**: Identify seasonal pricing patterns

## Best Practices

1. **Rate Limiting**: Built-in delays to avoid overwhelming the server
2. **Error Handling**: Robust error handling for network issues
3. **Data Validation**: Clean and validate scraped data
4. **Logging**: Comprehensive logging for debugging
5. **Respectful Scraping**: Follow ethical scraping practices

## Troubleshooting

### Common Issues

1. **Browser not found**: Install Playwright browsers
   ```bash
   playwright install chromium
   ```

2. **MongoDB connection failed**: Ensure MongoDB is running
   ```bash
   # Check if MongoDB is running
   brew services list | grep mongodb
   
   # Start MongoDB if not running
   brew services start mongodb-community
   ```

3. **No data scraped**: Website structure may have changed
   - Check logs for specific errors
   - Update selectors in scraper code

4. **Database connection errors**: Verify MongoDB configuration
   ```bash
   # Test MongoDB connection
   python -c "from src.models.database_models import DatabaseManager; db = DatabaseManager(); print('MongoDB connection successful')"
   ```

5. **Missing dependencies**: Install MongoDB drivers
   ```bash
   uv pip install pymongo motor
   ```

## MongoDB Management

### Database Administration
- Use **MongoDB Compass** for GUI database management
- Monitor logs: `tail -f /usr/local/var/log/mongodb/mongo.log`
- View database stats in MongoDB shell: `mongo redbus_fares`

### Performance Tips
- Collections are pre-indexed for optimal query performance
- Use aggregation pipelines for complex analytics
- Consider sharding for large datasets

### Package Management with uv
- **Fast**: uv is significantly faster than pip
- **Reliable**: Better dependency resolution  
- **Compatible**: Drop-in replacement for pip commands
- **Modern**: Uses pyproject.toml for configuration

#### Common uv Commands
```bash
# Install project in editable mode
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"

# Add a new package
uv add package_name

# Remove packages
uv remove package_name

# Sync dependencies
uv pip sync requirements.txt

# Run development tools
uv run black src/          # Code formatting
uv run flake8 src/         # Linting
uv run mypy src/           # Type checking
uv run pytest             # Testing
```

## Legal & Ethical Considerations

- This tool is for educational and research purposes
- Respect website terms of service
- Implement appropriate delays between requests
- Do not overload the target server
- Use scraped data responsibly

## Documentation

For detailed MongoDB setup, configuration, and usage instructions, see **[CLAUDE.md](CLAUDE.md)**.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test MongoDB integration
5. Add tests if applicable
6. Submit a pull request

## License

This project is for educational purposes. Please respect RedBus's terms of service and use responsibly.
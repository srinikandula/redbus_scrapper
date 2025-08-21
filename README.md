# RedBus Fare Scraper for Dynamic Pricing

A Python project to scrape bus ticket fares from RedBus for building a dynamic pricing module. The scraper searches buses between source and destination combinations, navigates to search results, extracts seat/fare information, and builds a database for fare analysis and dynamic pricing strategies.

## Features

- **Automated Bus Search**: Search buses between any source-destination combination
- **Detailed Fare Extraction**: Extract seat categories, prices, and availability
- **Database Storage**: Store fare data in SQLite database with proper schema
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
├── data/                          # Database and export files
├── logs/                          # Log files
├── main.py                        # Main application entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd redbus_scrapper
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Create necessary directories**:
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
DATABASE_PATH=data/redbus_fares.db
```

## Database Schema

The project uses SQLite with the following main tables:

- **routes**: Source-destination combinations
- **bus_operators**: Bus company information
- **bus_services**: Bus service details (timings, type, etc.)
- **fare_data**: Seat categories, prices, and availability
- **scraping_sessions**: Track scraping operations

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

2. **No data scraped**: Website structure may have changed
   - Check logs for specific errors
   - Update selectors in scraper code

3. **Database errors**: Ensure data directory exists
   ```bash
   mkdir -p data
   ```

## Legal & Ethical Considerations

- This tool is for educational and research purposes
- Respect website terms of service
- Implement appropriate delays between requests
- Do not overload the target server
- Use scraped data responsibly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Please respect RedBus's terms of service and use responsibly.
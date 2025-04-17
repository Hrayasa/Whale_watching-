# Whale Watch: Habitat Preferences and Migration Patterns Analysis

This project analyzes whale sighting and tracking data from the OBIS-SEAMAP database to identify habitat preferences and migration patterns of various whale species.

## Project Structure

```
whale_watch/
├── data/                  # Raw and processed data
├── src/                   # Source code
│   ├── data_acquisition/  # Data fetching and cleaning
│   ├── analysis/          # Data analysis modules
│   ├── visualization/     # Visualization tools
│   └── utils/            # Utility functions
├── notebooks/            # Jupyter notebooks for analysis
└── tests/               # Test files
```

## Features

- Data acquisition from OBIS-SEAMAP database
- Data cleaning and preprocessing
- Spatial and temporal analysis of whale sightings
- Interactive visualization of migration patterns
- Habitat preference analysis
- Environmental data integration (optional)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the data acquisition script:
   ```bash
   python src/data_acquisition/fetch_data.py
   ```
2. Process the data:
   ```bash
   python src/data_acquisition/clean_data.py
   ```
3. Start the visualization dashboard:
   ```bash
   python src/visualization/dashboard.py
   ```

## Data Sources

- OBIS-SEAMAP database
- NOAA environmental data 
- NASA satellite data 

## License

MIT License 

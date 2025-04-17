import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path

from utils.api_utils import OBISSEAMAPClient
from data_acquisition.clean_data import WhaleDataCleaner
from analysis.habitat_analysis import WhaleHabitatAnalyzer
from visualization.map_visualizer import WhaleMapVisualizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Initialize clients and analyzers
    api_client = OBISSEAMAPClient()
    data_cleaner = WhaleDataCleaner()
    
    # Fetch whale data
    logger.info("Fetching whale data from OBIS-SEAMAP...")
    whale_species = ['Megaptera novaeangliae']  # Humpback whale
    date_range = {
        'start': '2010-01-01',
        'end': '2020-12-31'
    }
    
    raw_data = api_client.fetch_whale_data(
        species=whale_species,
        date_range=date_range
    )
    
    if raw_data.empty:
        logger.error("No data retrieved from API")
        return
    
    # Save raw data
    raw_data_path = data_dir / 'raw_whale_data.csv'
    raw_data.to_csv(raw_data_path, index=False)
    logger.info(f"Raw data saved to {raw_data_path}")
    
    # Clean data
    logger.info("Cleaning whale data...")
    cleaned_data = data_cleaner.clean_data(raw_data)
    
    if cleaned_data.empty:
        logger.error("No data after cleaning")
        return
    
    # Save cleaned data
    cleaned_data_path = data_dir / 'cleaned_whale_data.csv'
    cleaned_data.to_csv(cleaned_data_path, index=False)
    logger.info(f"Cleaned data saved to {cleaned_data_path}")
    
    # Initialize analyzers
    habitat_analyzer = WhaleHabitatAnalyzer(cleaned_data)
    map_visualizer = WhaleMapVisualizer(cleaned_data)
    
    # Analyze habitat preferences
    logger.info("Analyzing habitat preferences...")
    habitat_metrics = habitat_analyzer.analyze_habitat_preferences(
        species=whale_species[0],
        time_period='season'
    )
    
    # Analyze migration patterns
    logger.info("Analyzing migration patterns...")
    migration_metrics = habitat_analyzer.analyze_migration_patterns(
        species=whale_species[0]
    )
    
    # Create visualizations
    logger.info("Creating visualizations...")
    
    # Create interactive map
    map_fig = map_visualizer.create_interactive_map(
        species=whale_species[0],
        time_range=date_range,
        show_heatmap=True,
        show_tracks=True
    )
    
    # Save map
    map_path = data_dir / 'whale_sightings_map.html'
    map_fig.save(str(map_path))
    logger.info(f"Map saved to {map_path}")
    
    # Create temporal plot
    temporal_fig = map_visualizer.create_temporal_plot(
        species=whale_species[0],
        time_period='month'
    )
    
    # Save temporal plot
    temporal_path = data_dir / 'temporal_distribution.html'
    temporal_fig.write_html(str(temporal_path))
    logger.info(f"Temporal plot saved to {temporal_path}")
    
    # Create habitat preference plot
    habitat_fig = map_visualizer.create_habitat_preference_plot(
        species=whale_species[0],
        time_period='season'
    )
    
    # Save habitat preference plot
    habitat_path = data_dir / 'habitat_preferences.html'
    habitat_fig.write_html(str(habitat_path))
    logger.info(f"Habitat preference plot saved to {habitat_path}")
    
    # Print summary statistics
    logger.info("\nSummary Statistics:")
    logger.info(f"Total sightings: {len(cleaned_data)}")
    logger.info(f"Unique locations: {len(cleaned_data[['latitude', 'longitude']].drop_duplicates())}")
    logger.info(f"Time span: {cleaned_data['eventdate'].min()} to {cleaned_data['eventdate'].max()}")
    
    if migration_metrics:
        logger.info(f"Total migration distance: {migration_metrics['total_distance']:.2f} km")
    
    logger.info("\nAnalysis complete! Check the data directory for results.")

if __name__ == "__main__":
    main() 
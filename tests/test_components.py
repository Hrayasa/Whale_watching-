import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from src.utils.api_utils import OBISSEAMAPClient
from src.data_acquisition.clean_data import WhaleDataCleaner
from src.analysis.habitat_analysis import WhaleHabitatAnalyzer
from src.visualization.map_visualizer import WhaleMapVisualizer

class TestWhaleWatchComponents(unittest.TestCase):
    def setUp(self):
        # Create sample data for testing
        dates = pd.date_range(start='2010-01-01', periods=10)
        self.sample_data = pd.DataFrame({
            'scientificname': ['Megaptera novaeangliae'] * 10,
            'latitude': np.random.uniform(-90, 90, 10),
            'longitude': np.random.uniform(-180, 180, 10),
            'eventdate': dates,
            'individualcount': np.random.randint(1, 5, 10),
            'year': dates.year,
            'month': dates.month,
            'season': [
                'Winter' if m in [12, 1, 2] else
                'Spring' if m in [3, 4, 5] else
                'Summer' if m in [6, 7, 8] else
                'Autumn' for m in dates.month
            ]
        })
        
        # Initialize components
        self.data_cleaner = WhaleDataCleaner()
        self.habitat_analyzer = WhaleHabitatAnalyzer(self.sample_data)
        self.map_visualizer = WhaleMapVisualizer(self.sample_data)
    
    def test_data_cleaning(self):
        """Test the data cleaning functionality."""
        cleaned_data = self.data_cleaner.clean_data(self.sample_data)
        
        # Check if required columns are present
        self.assertTrue(all(col in cleaned_data.columns for col in 
                          ['scientificname', 'latitude', 'longitude', 'eventdate']))
        
        # Check if coordinates are within valid ranges
        self.assertTrue(all(cleaned_data['latitude'].between(-90, 90)))
        self.assertTrue(all(cleaned_data['longitude'].between(-180, 180)))
        
        # Check if dates are properly converted
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(cleaned_data['eventdate']))
    
    def test_habitat_analysis(self):
        """Test the habitat analysis functionality."""
        # Test habitat preferences analysis
        habitat_metrics = self.habitat_analyzer.analyze_habitat_preferences(
            species='Megaptera novaeangliae'
        )
        
        self.assertIn('total_sightings', habitat_metrics)
        self.assertIn('unique_locations', habitat_metrics)
        self.assertIn('hotspot_count', habitat_metrics)
        
        # Test migration patterns analysis
        migration_metrics = self.habitat_analyzer.analyze_migration_patterns(
            species='Megaptera novaeangliae'
        )
        
        self.assertIn('centroids', migration_metrics)
        self.assertIn('total_distance', migration_metrics)
        self.assertIn('migration_corridors', migration_metrics)
    
    def test_visualization(self):
        """Test the visualization functionality."""
        # Test map creation
        map_fig = self.map_visualizer.create_interactive_map(
            species='Megaptera novaeangliae'
        )
        self.assertIsNotNone(map_fig)
        
        # Test temporal plot creation
        temporal_fig = self.map_visualizer.create_temporal_plot(
            species='Megaptera novaeangliae'
        )
        self.assertIsNotNone(temporal_fig)
        
        # Test habitat preference plot creation
        habitat_fig = self.map_visualizer.create_habitat_preference_plot(
            species='Megaptera novaeangliae'
        )
        self.assertIsNotNone(habitat_fig)
    
    def test_api_client(self):
        """Test the API client functionality."""
        api_client = OBISSEAMAPClient()
        
        # Test species list retrieval
        species_list = api_client.get_species_list()
        self.assertIsInstance(species_list, list)
        
        # Test data fetching
        date_range = {
            'start': '2010-01-01',
            'end': '2010-12-31'
        }
        whale_data = api_client.fetch_whale_data(
            species=['Megaptera novaeangliae'],
            date_range=date_range
        )
        self.assertIsInstance(whale_data, pd.DataFrame)

if __name__ == '__main__':
    unittest.main() 
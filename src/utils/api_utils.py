import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OBISSEAMAPClient:
    """Client for interacting with the OBIS-SEAMAP API."""
    
    BASE_URL = "https://seamap.env.duke.edu/api/v1/observations"
    
    def __init__(self, use_sample_data: bool = True):
        """
        Initialize the API client.
        
        Args:
            use_sample_data: If True, use generated sample data instead of real API
        """
        self.use_sample_data = use_sample_data
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'WhaleWatch/1.0 (Research Project)'
        })
        
        # Define common whale species with their scientific and common names
        self.whale_species = [
            {
                "scientific_name": "Megaptera novaeangliae",
                "common_name": "Humpback Whale"
            },
            {
                "scientific_name": "Balaenoptera musculus",
                "common_name": "Blue Whale"
            },
            {
                "scientific_name": "Balaenoptera physalus",
                "common_name": "Fin Whale"
            },
            {
                "scientific_name": "Eubalaena glacialis",
                "common_name": "North Atlantic Right Whale"
            },
            {
                "scientific_name": "Eschrichtius robustus",
                "common_name": "Gray Whale"
            },
            {
                "scientific_name": "Physeter macrocephalus",
                "common_name": "Sperm Whale"
            },
            {
                "scientific_name": "Orcinus orca",
                "common_name": "Killer Whale (Orca)"
            },
            {
                "scientific_name": "Balaenoptera borealis",
                "common_name": "Sei Whale"
            },
            {
                "scientific_name": "Balaenoptera acutorostrata",
                "common_name": "Minke Whale"
            },
            {
                "scientific_name": "Delphinapterus leucas",
                "common_name": "Beluga Whale"
            }
        ]
    
    def get_species_list(self) -> List[Dict[str, str]]:
        """Get a list of whale species with both scientific and common names."""
        try:
            logger.info(f"Returning {len(self.whale_species)} predefined whale species")
            return self.whale_species
            
        except Exception as e:
            logger.error(f"Error getting species list: {e}")
            return []
    
    def _generate_sample_data(self, 
                            species: List[str],
                            date_range: Dict[str, str]) -> pd.DataFrame:
        """
        Generate sample whale sighting data for testing.
        
        Args:
            species: List of species scientific names
            date_range: Dictionary with 'start' and 'end' dates
            
        Returns:
            DataFrame containing sample whale sighting data
        """
        logger.info("Generating sample data...")
        
        # Convert date strings to datetime
        start_date = pd.to_datetime(date_range['start'])
        end_date = pd.to_datetime(date_range['end'])
        date_range_days = (end_date - start_date).days
        
        # Generate random sightings
        n_sightings = 100
        records = []
        
        for _ in range(n_sightings):
            # Random date within range
            random_days = random.randint(0, date_range_days)
            sighting_date = start_date + timedelta(days=random_days)
            
            # Random species from the provided list
            species_name = species[0] if species else random.choice(self.whale_species)['scientific_name']
            
            # Random location (focusing on major whale habitats)
            # North Atlantic
            lat = random.uniform(25, 65)
            lon = random.uniform(-80, -10)
            
            records.append({
                'scientificname': species_name,
                'eventdate': sighting_date,
                'latitude': lat,
                'longitude': lon,
                'individualcount': random.randint(1, 5)
            })
        
        df = pd.DataFrame(records)
        logger.info(f"Generated {len(df)} sample whale sightings")
        return df
    
    def fetch_whale_data(self,
                        species: Optional[List[str]] = None,
                        date_range: Optional[Dict[str, str]] = None,
                        bbox: Optional[List[float]] = None) -> pd.DataFrame:
        """
        Fetch whale sighting data from OBIS-SEAMAP or generate sample data.
        
        Args:
            species: List of species scientific names
            date_range: Dictionary with 'start' and 'end' dates (YYYY-MM-DD)
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            
        Returns:
            DataFrame containing whale sighting data
        """
        if self.use_sample_data:
            return self._generate_sample_data(species, date_range)
        
        params = {
            'format': 'json',
            'taxon': species[0] if species else None,
            'start_date': date_range['start'] if date_range else None,
            'end_date': date_range['end'] if date_range else None
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        logger.info(f"Fetching data with parameters: {params}")
        
        try:
            logger.info(f"Making request to {self.BASE_URL}")
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content type: {response.headers.get('content-type', 'unknown')}")
            
            # Parse JSON response
            data = response.json()
            logger.info(f"Received {len(data.get('features', []))} records")
            
            if not data.get('features'):
                logger.warning("No features found in response")
                return pd.DataFrame()
            
            # Convert GeoJSON features to DataFrame
            records = []
            for feature in data['features']:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                record = {
                    'scientificname': props.get('taxon'),
                    'eventdate': props.get('date'),
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'individualcount': props.get('count', 1)
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            
            # Convert date
            df['eventdate'] = pd.to_datetime(df['eventdate'], errors='coerce')
            
            # Remove rows with invalid coordinates
            df = df[
                df['latitude'].between(-90, 90) &
                df['longitude'].between(-180, 180)
            ]
            
            logger.info(f"Successfully processed {len(df)} whale sightings")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching whale data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response text: {e.response.text}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error processing whale data: {e}")
            return pd.DataFrame() 
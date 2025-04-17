import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhaleDataCleaner:
    """Class for cleaning and preprocessing whale sighting data."""
    
    def __init__(self):
        self.required_columns = [
            'scientificname',
            'latitude',
            'longitude',
            'eventdate',
            'individualcount'
        ]
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess the whale sighting data.
        
        Args:
            df: Raw DataFrame from OBIS-SEAMAP
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return df
        
        # Create a copy to avoid modifying the original
        df_clean = df.copy()
        
        # Ensure required columns exist
        missing_cols = [col for col in self.required_columns if col not in df_clean.columns]
        if missing_cols:
            logger.warning(f"Missing columns will be created: {missing_cols}")
            for col in missing_cols:
                if col == 'individualcount':
                    df_clean[col] = 1  # Assume single individual if not specified
                else:
                    df_clean[col] = None
        
        # Convert date to datetime
        df_clean['eventdate'] = pd.to_datetime(df_clean['eventdate'], errors='coerce')
        
        # Handle missing values
        df_clean = self._handle_missing_values(df_clean)
        
        # Remove duplicates
        df_clean = self._remove_duplicates(df_clean)
        
        # Clean coordinates
        df_clean = self._clean_coordinates(df_clean)
        
        # Add derived features
        df_clean = self._add_derived_features(df_clean)
        
        return df_clean
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset."""
        # Drop rows with missing coordinates or dates
        df = df.dropna(subset=['latitude', 'longitude', 'eventdate'])
        
        # Fill missing individual counts with 1
        df['individualcount'] = df['individualcount'].fillna(1)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records."""
        return df.drop_duplicates(subset=['scientificname', 'latitude', 'longitude', 'eventdate'])
    
    def _clean_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate geographic coordinates."""
        # Convert to numeric
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        # Remove invalid coordinates
        df = df[
            (df['latitude'].between(-90, 90)) &
            (df['longitude'].between(-180, 180))
        ]
        
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features to the dataset."""
        # Extract temporal features
        df['year'] = df['eventdate'].dt.year
        df['month'] = df['eventdate'].dt.month
        df['season'] = df['month'].apply(self._get_season)
        
        # Add hemisphere information
        df['hemisphere'] = np.where(df['latitude'] >= 0, 'Northern', 'Southern')
        
        return df
    
    @staticmethod
    def _get_season(month: int) -> str:
        """Convert month to season."""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Autumn' 
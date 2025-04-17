import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from scipy.stats import gaussian_kde
from sklearn.cluster import DBSCAN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhaleHabitatAnalyzer:
    """Class for analyzing whale habitat preferences and migration patterns."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._validate_data()
    
    def _validate_data(self):
        """Validate the input data."""
        required_columns = ['scientificname', 'latitude', 'longitude', 'eventdate']
        missing_cols = [col for col in required_columns if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def analyze_habitat_preferences(self, 
                                  species: str = None,
                                  time_period: str = None) -> Dict:
        """
        Analyze habitat preferences for a specific species or all species.
        
        Args:
            species: Scientific name of the species to analyze
            time_period: Time period to consider ('year', 'season', or None)
            
        Returns:
            Dictionary containing habitat preference metrics
        """
        # Filter data if species is specified
        df_filtered = self.df.copy()
        if species:
            df_filtered = df_filtered[df_filtered['scientificname'] == species]
        
        # Group by time period if specified
        if time_period:
            if time_period == 'year':
                group_col = 'year'
            elif time_period == 'season':
                group_col = 'season'
            else:
                raise ValueError("time_period must be 'year' or 'season'")
            
            results = {}
            for period, group in df_filtered.groupby(group_col):
                results[period] = self._calculate_habitat_metrics(group)
            return results
        else:
            return self._calculate_habitat_metrics(df_filtered)
    
    def _calculate_habitat_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate habitat preference metrics for a given dataset."""
        if df.empty:
            return {}
            
        # Calculate density using kernel density estimation
        coordinates = df[['longitude', 'latitude']].values
        kde = gaussian_kde(coordinates.T)
        
        # Find hotspots using DBSCAN clustering
        clustering = DBSCAN(eps=1.0, min_samples=5).fit(coordinates)
        hotspots = df[clustering.labels_ != -1]
        
        return {
            'total_sightings': len(df),
            'unique_locations': len(df[['latitude', 'longitude']].drop_duplicates()),
            'hotspot_count': len(hotspots),
            'density_estimate': kde,
            'hotspots': hotspots
        }
    
    def analyze_migration_patterns(self, 
                                 species: str,
                                 time_window: str = 'month') -> Dict:
        """
        Analyze migration patterns for a specific species.
        
        Args:
            species: Scientific name of the species
            time_window: Time window for analysis ('month' or 'season')
            
        Returns:
            Dictionary containing migration pattern metrics
        """
        # Filter data for the specified species
        df_species = self.df[self.df['scientificname'] == species].copy()
        
        if df_species.empty:
            logger.warning(f"No data found for species: {species}")
            return {}
        
        # Calculate centroids for each time period
        centroids = self._calculate_centroids(df_species, time_window)
        
        # Calculate migration metrics
        metrics = {
            'centroids': centroids,
            'total_distance': self._calculate_total_distance(centroids),
            'seasonal_ranges': self._calculate_seasonal_ranges(df_species),
            'migration_corridors': self._identify_migration_corridors(df_species)
        }
        
        return metrics
    
    def _calculate_centroids(self, 
                           df: pd.DataFrame, 
                           time_window: str) -> pd.DataFrame:
        """Calculate centroids for each time period."""
        if time_window == 'month':
            group_col = 'month'
        else:
            group_col = 'season'
            
        centroids = df.groupby(group_col).agg({
            'latitude': 'mean',
            'longitude': 'mean',
            'eventdate': 'count'
        }).reset_index()
        
        centroids.columns = [group_col, 'centroid_lat', 'centroid_lon', 'sighting_count']
        return centroids
    
    def _calculate_total_distance(self, centroids: pd.DataFrame) -> float:
        """Calculate total migration distance based on centroids."""
        if len(centroids) < 2:
            return 0.0
            
        # Calculate distances between consecutive centroids
        distances = []
        for i in range(len(centroids) - 1):
            lat1, lon1 = centroids.iloc[i][['centroid_lat', 'centroid_lon']]
            lat2, lon2 = centroids.iloc[i+1][['centroid_lat', 'centroid_lon']]
            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(distance)
            
        return sum(distances)
    
    def _calculate_seasonal_ranges(self, df: pd.DataFrame) -> Dict:
        """Calculate seasonal ranges for the species."""
        seasonal_ranges = {}
        for season, group in df.groupby('season'):
            lat_range = (group['latitude'].min(), group['latitude'].max())
            lon_range = (group['longitude'].min(), group['longitude'].max())
            seasonal_ranges[season] = {
                'latitude_range': lat_range,
                'longitude_range': lon_range
            }
        return seasonal_ranges
    
    def _identify_migration_corridors(self, df: pd.DataFrame) -> List[Dict]:
        """Identify potential migration corridors based on sighting density."""
        # Use DBSCAN to identify clusters of sightings
        coordinates = df[['longitude', 'latitude']].values
        clustering = DBSCAN(eps=1.0, min_samples=5).fit(coordinates)
        
        corridors = []
        for label in set(clustering.labels_):
            if label == -1:  # Skip noise points
                continue
                
            cluster_points = df[clustering.labels_ == label]
            corridor = {
                'points': cluster_points[['latitude', 'longitude']].values.tolist(),
                'sighting_count': len(cluster_points),
                'time_span': (cluster_points['eventdate'].min(), 
                            cluster_points['eventdate'].max())
            }
            corridors.append(corridor)
            
        return corridors
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate the Haversine distance between two points."""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c 
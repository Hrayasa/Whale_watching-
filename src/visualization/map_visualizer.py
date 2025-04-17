import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import logging
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhaleMapVisualizer:
    """Class for creating interactive visualizations of whale data."""
    
    # Define India's bounding box
    INDIA_BBOX = {
        'min_lat': 6.5,   # Southern tip of India
        'max_lat': 35.5,  # Northern boundary including Kashmir
        'min_lon': 68.0,  # Western boundary
        'max_lon': 97.5   # Eastern boundary including Andaman & Nicobar
    }
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._validate_data()
    
    def _validate_data(self):
        """Validate the input data."""
        required_columns = ['scientificname', 'latitude', 'longitude', 'eventdate']
        missing_cols = [col for col in required_columns if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def create_interactive_map(self,
                             species: Optional[str] = None,
                             time_range: Optional[Dict[str, datetime]] = None,
                             show_heatmap: bool = True,
                             show_tracks: bool = True) -> go.Figure:
        """
        Create an interactive map showing whale sightings and migration patterns.
        
        Args:
            species: Filter by specific species
            time_range: Dictionary with 'start' and 'end' dates
            show_heatmap: Whether to show density heatmap
            show_tracks: Whether to show migration tracks
            
        Returns:
            plotly.graph_objects.Figure
        """
        # Filter data based on parameters
        df_filtered = self._filter_data(species, time_range)
        
        if df_filtered.empty:
            # Return empty figure if no data
            return go.Figure()
        
        # Create base map
        fig = go.Figure()
        
        # Split data into Indian region and rest of the world
        df_india = df_filtered[
            (df_filtered['latitude'].between(self.INDIA_BBOX['min_lat'], self.INDIA_BBOX['max_lat'])) &
            (df_filtered['longitude'].between(self.INDIA_BBOX['min_lon'], self.INDIA_BBOX['max_lon']))
        ]
        df_world = df_filtered[~df_filtered.index.isin(df_india.index)]
        
        # Add Indian region sightings with different color
        if not df_india.empty:
            fig.add_trace(go.Scattermapbox(
                lon=df_india['longitude'],
                lat=df_india['latitude'],
                mode='markers',
                marker=dict(
                    size=10,
                    opacity=0.8,
                    color='red'  # Highlight Indian region sightings
                ),
                text=[
                    f"Species: {row['scientificname']}<br>"
                    f"Date: {row['eventdate'].strftime('%Y-%m-%d')}<br>"
                    f"Count: {row.get('individualcount', 1)}<br>"
                    f"Region: Indian Waters"
                    for _, row in df_india.iterrows()
                ],
                hoverinfo='text',
                name='Sightings (Indian Waters)'
            ))
        
        # Add rest of world sightings
        if not df_world.empty:
            fig.add_trace(go.Scattermapbox(
                lon=df_world['longitude'],
                lat=df_world['latitude'],
                mode='markers',
                marker=dict(
                    size=8,
                    opacity=0.6,
                    color='blue'
                ),
                text=[
                    f"Species: {row['scientificname']}<br>"
                    f"Date: {row['eventdate'].strftime('%Y-%m-%d')}<br>"
                    f"Count: {row.get('individualcount', 1)}<br>"
                    f"Region: International Waters"
                    for _, row in df_world.iterrows()
                ],
                hoverinfo='text',
                name='Sightings (International Waters)'
            ))
        
        # Add migration tracks if requested
        if show_tracks:
            for _, group in df_filtered.groupby('scientificname'):
                group = group.sort_values('eventdate')
                fig.add_trace(go.Scattermapbox(
                    lon=group['longitude'],
                    lat=group['latitude'],
                    mode='lines',
                    line=dict(
                        width=2,
                        color='rgba(255, 165, 0, 0.6)'  # Semi-transparent orange
                    ),
                    name='Migration Track'
                ))
        
        # Add density heatmap if requested
        if show_heatmap and len(df_filtered) > 1:
            fig.add_trace(go.Densitymapbox(
                lat=df_filtered['latitude'],
                lon=df_filtered['longitude'],
                z=df_filtered['individualcount'],
                radius=30,
                colorscale='Viridis',
                name='Density',
                opacity=0.5
            ))
        
        # Center map on India by default
        center_lat = (self.INDIA_BBOX['min_lat'] + self.INDIA_BBOX['max_lat']) / 2
        center_lon = (self.INDIA_BBOX['min_lon'] + self.INDIA_BBOX['max_lon']) / 2
        
        # Update layout with Mapbox
        fig.update_layout(
            title=f'Whale Sightings Map - {species if species else "All Species"}',
            mapbox=dict(
                style='carto-positron',  # Light map style
                center=dict(lat=center_lat, lon=center_lon),
                zoom=4  # Closer zoom to show Indian region in detail
            ),
            showlegend=True,
            margin=dict(l=0, r=0, t=30, b=0),
            width=800,
            height=600
        )
        
        return fig
    
    def _filter_data(self,
                    species: Optional[str],
                    time_range: Optional[Dict[str, datetime]]) -> pd.DataFrame:
        """Filter data based on species and time range."""
        df_filtered = self.df.copy()
        
        if species:
            df_filtered = df_filtered[df_filtered['scientificname'] == species]
        
        if time_range:
            df_filtered = df_filtered[
                (df_filtered['eventdate'] >= time_range['start']) &
                (df_filtered['eventdate'] <= time_range['end'])
            ]
        
        return df_filtered
    
    def create_temporal_plot(self,
                           species: Optional[str] = None,
                           time_period: str = 'month') -> go.Figure:
        """
        Create a temporal plot of whale sightings.
        
        Args:
            species: Filter by specific species
            time_period: Time period for aggregation ('month' or 'year')
            
        Returns:
            plotly.graph_objects.Figure
        """
        # Filter data
        df_filtered = self._filter_data(species, None)
        
        # Group by time period
        if time_period == 'month':
            df_grouped = df_filtered.groupby(['year', 'month']).size().reset_index(name='count')
            df_grouped['date'] = pd.to_datetime(
                df_grouped[['year', 'month']].assign(day=1)
            )
        else:
            df_grouped = df_filtered.groupby('year').size().reset_index(name='count')
            df_grouped['date'] = pd.to_datetime(df_grouped['year'], format='%Y')
        
        # Create plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_grouped['date'],
            y=df_grouped['count'],
            mode='lines+markers',
            name='Sightings'
        ))
        
        # Update layout
        fig.update_layout(
            title='Temporal Distribution of Whale Sightings',
            xaxis_title='Date',
            yaxis_title='Number of Sightings',
            hovermode='x unified'
        )
        
        return fig
    
    def create_habitat_preference_plot(self,
                                     species: str,
                                     time_period: str = 'season') -> go.Figure:
        """
        Create a plot showing habitat preferences by season or year.
        
        Args:
            species: Species to analyze
            time_period: Time period for grouping ('season' or 'year')
            
        Returns:
            plotly.graph_objects.Figure
        """
        # Filter data for species
        df_species = self.df[self.df['scientificname'] == species].copy()
        
        # Group by time period and calculate statistics
        df_grouped = df_species.groupby(time_period).agg({
            'latitude': ['mean', 'std'],
            'longitude': ['mean', 'std']
        }).reset_index()
        
        # Create plot
        fig = go.Figure()
        
        # Add error bars for latitude
        fig.add_trace(go.Scatter(
            x=df_grouped[time_period],
            y=df_grouped[('latitude', 'mean')],
            error_y=dict(
                type='data',
                array=df_grouped[('latitude', 'std')],
                visible=True
            ),
            name='Latitude',
            mode='lines+markers'
        ))
        
        # Add error bars for longitude
        fig.add_trace(go.Scatter(
            x=df_grouped[time_period],
            y=df_grouped[('longitude', 'mean')],
            error_y=dict(
                type='data',
                array=df_grouped[('longitude', 'std')],
                visible=True
            ),
            name='Longitude',
            mode='lines+markers'
        ))
        
        # Update layout
        fig.update_layout(
            title=f'Habitat Preferences for {species} by {time_period}',
            xaxis_title=time_period.capitalize(),
            yaxis_title='Coordinates',
            hovermode='x unified'
        )
        
        return fig 
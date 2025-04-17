import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
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

# Initialize the API client with sample data
api_client = OBISSEAMAPClient(use_sample_data=True)

# Initialize Dash app
app = dash.Dash(__name__, title='Whale Watch Dashboard')

# Get initial species list
species_list = api_client.get_species_list()
species_options = [
    {'label': f"{species['common_name']} ({species['scientific_name']})", 
     'value': species['scientific_name']} 
    for species in species_list
]

# Define the layout
app.layout = html.Div([
    html.H1('Whale Watch: Habitat Preferences and Migration Patterns', 
            style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Controls section
    html.Div([
        html.Div([
            html.Label('Select Species:'),
            dcc.Dropdown(
                id='species-dropdown',
                options=species_options,
                value=species_options[0]['value'] if species_options else None,
                multi=False,
                style={'width': '100%', 'minWidth': '300px'},
                clearable=False
            ),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Date Range:'),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=datetime(2000, 1, 1),
                max_date_allowed=datetime.now(),
                start_date=datetime(2010, 1, 1),
                end_date=datetime(2020, 12, 31),
                style={'width': '100%'}
            ),
        ], style={'width': '40%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Analysis Type:'),
            dcc.RadioItems(
                id='analysis-type',
                options=[
                    {'label': 'Habitat Preferences', 'value': 'habitat'},
                    {'label': 'Migration Patterns', 'value': 'migration'}
                ],
                value='habitat',
                style={'marginTop': '10px'}
            ),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'border': '1px solid #ddd', 'padding': '20px', 'margin': '10px', 'borderRadius': '5px'}),
    
    # Loading state
    dcc.Loading(
        id="loading",
        type="circle",
        children=[
            # Main content area
            html.Div([
                # Map visualization
                html.Div([
                    html.H3('Whale Sightings Map', style={'textAlign': 'center'}),
                    dcc.Graph(id='whale-map')
                ], style={'width': '60%', 'display': 'inline-block', 'padding': '10px'}),
                
                # Analysis results
                html.Div([
                    html.H3('Analysis Results', style={'textAlign': 'center'}),
                    html.Div(id='analysis-results')
                ], style={'width': '35%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),
            ]),
            
            # Temporal analysis
            html.Div([
                html.H3('Temporal Analysis', style={'textAlign': 'center'}),
                dcc.Graph(id='temporal-plot')
            ], style={'padding': '20px', 'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),
            
            # Habitat preferences
            html.Div([
                html.H3('Habitat Preferences', style={'textAlign': 'center'}),
                dcc.Graph(id='habitat-plot')
            ], style={'padding': '20px', 'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),
        ]
    ),
    
    # Error message area
    html.Div(id='error-message', style={'color': 'red', 'margin': '10px', 'textAlign': 'center'})
])

@app.callback(
    [Output('whale-map', 'figure'),
     Output('analysis-results', 'children'),
     Output('temporal-plot', 'figure'),
     Output('habitat-plot', 'figure'),
     Output('error-message', 'children')],
    [Input('species-dropdown', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('analysis-type', 'value')]
)
def update_visualizations(species, start_date, end_date, analysis_type):
    if not species:
        return {}, html.Div("Please select a species"), {}, {}, "No species selected"
    
    try:
        # Fetch and process data
        date_range = {
            'start': start_date,
            'end': end_date
        }
        
        logger.info(f"Fetching data for {species} from {start_date} to {end_date}")
        raw_data = api_client.fetch_whale_data(
            species=[species],
            date_range=date_range
        )
        
        if raw_data.empty:
            return {}, html.Div("No data available"), {}, {}, "No data available for the selected criteria"
        
        # Clean data
        data_cleaner = WhaleDataCleaner()
        cleaned_data = data_cleaner.clean_data(raw_data)
        
        if cleaned_data.empty:
            return {}, html.Div("No valid data after cleaning"), {}, {}, "No valid data after cleaning"
        
        # Initialize analyzers
        habitat_analyzer = WhaleHabitatAnalyzer(cleaned_data)
        map_visualizer = WhaleMapVisualizer(cleaned_data)
        
        # Create visualizations
        map_fig = map_visualizer.create_interactive_map(
            species=species,
            time_range=date_range,
            show_heatmap=True,
            show_tracks=(analysis_type == 'migration')
        )
        
        temporal_fig = map_visualizer.create_temporal_plot(
            species=species,
            time_period='month'
        )
        
        habitat_fig = map_visualizer.create_habitat_preference_plot(
            species=species,
            time_period='season'
        )
        
        # Generate analysis results
        if analysis_type == 'habitat':
            metrics = habitat_analyzer.analyze_habitat_preferences(
                species=species,
                time_period='season'
            )
            results = html.Div([
                html.H4('Habitat Analysis Results'),
                html.P(f"Total sightings: {metrics.get('total_sightings', 0)}"),
                html.P(f"Unique locations: {metrics.get('unique_locations', 0)}"),
                html.P(f"Hotspot count: {metrics.get('hotspot_count', 0)}")
            ])
        else:
            metrics = habitat_analyzer.analyze_migration_patterns(species)
            results = html.Div([
                html.H4('Migration Analysis Results'),
                html.P(f"Total migration distance: {metrics.get('total_distance', 0):.2f} km"),
                html.P(f"Number of migration corridors: {len(metrics.get('migration_corridors', []))}")
            ])
        
        return map_fig, results, temporal_fig, habitat_fig, ""
        
    except Exception as e:
        logger.error(f"Error updating visualizations: {e}")
        return {}, html.Div("Error processing data"), {}, {}, f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True) 
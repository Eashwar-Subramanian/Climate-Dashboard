from flask import Flask, render_template, request, jsonify
import pandas as pd
import folium
from folium.plugins import TimestampedGeoJson, HeatMap
import plotly.express as px

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('weatherAUS.csv')

# Function to suggest policies based on climate data
def suggest_policies(location, data):
    policies = []

    # Heatwave Preparedness Policies
    if data['max_temp'] > 45:
        policies.append(f"Develop heatwave preparedness and public health awareness programs in {location}.")
        policies.append(f"Implement emergency response protocols, including cooling centers and distribution of resources during extreme heat events in {location}.")
        policies.append(f"Increase urban greening and develop heat-resilient infrastructure in {location} to reduce the urban heat island effect.")
    
    # Water Resource Management Policies
    if data['rainfall'] < 1000:  # Adjusted threshold
        policies.append(f"Promote rainwater harvesting and smart irrigation technologies in {location} due to moderate rainfall.")
        policies.append(f"Expand the use of recycled water for industrial and agricultural purposes in {location}.")
        policies.append(f"Implement seasonal water restrictions to prevent overuse during drought conditions in {location}.")

    # Flood Management Policies
    if data['rainfall'] > 800:
        policies.append(f"Upgrade stormwater drainage systems and develop flood barriers in {location} to protect against heavy rainfall.")
        policies.append(f"Encourage the use of green roofs and permeable pavements in {location} to reduce runoff and increase water absorption.")
        policies.append(f"Establish community-based flood monitoring systems with real-time data sharing in {location}.")

    # Air Quality and Pollution Control Policies
    if data['humidity_3pm'] > 70:
        policies.append(f"Enforce stricter regulations on industrial and vehicular emissions during high-humidity periods in {location}.")
        policies.append(f"Provide incentives for the adoption of renewable energy sources in {location}.")
        policies.append(f"Expand and improve public transportation networks in {location} to reduce vehicle emissions.")

    # Building Resilience Policies
    if data['avg_temp'] > 30:
        policies.append(f"Update building codes in {location} to include requirements for energy efficiency and heat resistance.")
        policies.append(f"Provide grants for retrofitting older buildings with energy-efficient technologies in {location}.")
        policies.append(f"Develop smart grid technologies to optimize electricity distribution in {location}.")

    # Biodiversity and Ecosystem Protection Policies
    policies.append(f"Implement habitat restoration programs in {location} to protect biodiversity.")
    policies.append(f"Develop wildlife corridors in {location} to ensure species can migrate and adapt to changing climate conditions.")
    policies.append(f"Monitor and control invasive species in {location} that may thrive due to changing temperatures and rainfall patterns.")

    # Community Engagement and Climate Education
    policies.append(f"Support the formation of community climate action groups in {location}.")
    policies.append(f"Integrate climate change education into school curriculums in {location}.")
    policies.append(f"Provide training programs for local businesses and government agencies in {location} on climate adaptation strategies.")

    # Climate Data Monitoring and Research
    policies.append(f"Increase the number of climate monitoring stations in {location} to collect data on temperature, rainfall, and air quality.")
    policies.append(f"Partner with research institutions in {location} to study local climate patterns and develop predictive models for policy planning.")
    policies.append(f"Create platforms for public access to climate data in {location} to enable informed decision-making.")

    # Default policy if none apply
    if not policies:
        policies.append(f"No specific policy recommendations based on the current data for {location}.")
    
    return policies

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Search route for location-based data
@app.route('/search', methods=['GET'])
def search():
    location = request.args.get('location')
    data = df[df['Location'].str.contains(location, case=False, na=False)]
    if not data.empty:
        summary = {
            'max_temp': data['MaxTemp'].max(),
            'min_temp': data['MinTemp'].min(),
            'avg_temp': data['Temp3pm'].mean(),
            'rainfall': data['Rainfall'].sum(),  # Total rainfall
            'humidity_3pm': data['Humidity3pm'].mean(),  # Average humidity at 3 PM
            'humidity_9am': data['Humidity9am'].mean()  # Average humidity at 9 AM
        }
        policies = suggest_policies(location, summary)
        summary['policies'] = policies
        return jsonify(summary)
    else:
        return jsonify({'error': 'Location not found'})

# GIS Map route
@app.route('/map')
def map_view():
    map_ = folium.Map(location=[-33.865143, 151.209900], zoom_start=4)
    folium.Marker([-33.865143, 151.209900], popup="Sydney").add_to(map_)
    map_html = map_._repr_html_()
    return render_template('map.html', map=map_html)

# Interactive GIS Map route with multiple markers and heatmap
@app.route('/interactive_map')
def interactive_map():
    # Sample data for multiple locations
    data = [
        {'lat': -33.865143, 'lng': 151.209900, 'popup': 'Sydney'},
        {'lat': -37.813629, 'lng': 144.963058, 'popup': 'Melbourne'},
        {'lat': -27.469770, 'lng': 153.025131, 'popup': 'Brisbane'}
    ]

    # Create a base map
    m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4)  # Center on Australia

    # Add markers
    for location in data:
        folium.Marker(
            location=[location['lat'], location['lng']],
            popup=location['popup']
        ).add_to(m)
    
    # Add heatmap
    heat_data = [[loc['lat'], loc['lng']] for loc in data]
    HeatMap(heat_data).add_to(m)
    
    return m._repr_html_()

# Temporal map route showing changes over time
@app.route('/temporal_map')
def temporal_map():
    data = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [151.2099, -33.865143]
                },
                'properties': {
                    'time': '2023-09-23T00:00:00Z',
                    'popup': 'Sydney Temperature Data'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [144.963058, -37.813629]
                },
                'properties': {
                    'time': '2023-09-24T00:00:00Z',
                    'popup': 'Melbourne Temperature Data'
                }
            }
        ]
    }

    m = folium.Map(location=[-33.865143, 151.209900], zoom_start=4)
    TimestampedGeoJson(
        data,
        period='P1D',  # daily data
        add_last_point=True,
        auto_play=True,
        loop=True
    ).add_to(m)
    return m._repr_html_()

# Rainfall chart route
@app.route('/rainfall_chart')
def rainfall_chart():
    location = request.args.get('location')
    data = df[df['Location'].str.contains(location, case=False, na=False)]

    if not data.empty:
        # Convert the 'Date' column to datetime
        data['Date'] = pd.to_datetime(data['Date'])
        
        # Sort by date
        data = data.sort_values('Date')

        # Calculate a 30-day moving average
        data['Rainfall_MA'] = data['Rainfall'].rolling(window=30).mean()

        # Create a figure
        fig = px.bar(data, x='Date', y='Rainfall', title=f'Rainfall in {location.upper()}',
                     labels={'Rainfall': 'Rainfall (mm)', 'Date': 'Date'})

        # Add a line plot for the moving average
        fig.add_scatter(x=data['Date'], y=data['Rainfall_MA'], mode='lines', name='30-Day Moving Average')

        # Update layout for better visuals
        fig.update_layout(
            title={
                'text': f"Rainfall in {location.upper()}",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Date',
            yaxis_title='Rainfall (mm)',
            template='plotly_white',
            hovermode='x'
        )

        # Add annotation for significant events
        max_rainfall = data['Rainfall'].max()
        max_date = data[data['Rainfall'] == max_rainfall]['Date'].iloc[0]

        fig.add_annotation(
            x=max_date,
            y=max_rainfall,
            text=f"Highest Rainfall: {max_rainfall} mm",
            showarrow=True,
            arrowhead=1
        )

                # Customize bar colors based on the intensity of rainfall
        colors = ['#3498db' if val < 50 else '#e74c3c' for val in data['Rainfall']]
        fig.update_traces(marker=dict(color=colors))

        graph_html = fig.to_html(full_html=False)
        return render_template('chart.html', graph_html=graph_html)
    else:
        return "Location not found"

# Temperature trends route
@app.route('/temperature_trend')
def temperature_trend():
    location = request.args.get('location')
    data = df[df['Location'].str.contains(location, case=False, na=False)]

    if not data.empty:
        # Convert the 'Date' column to datetime
        data['Date'] = pd.to_datetime(data['Date'])

        # Sort by date
        data = data.sort_values('Date')

        # Create a figure for temperature trends
        fig = px.line(data, x='Date', y=['MaxTemp', 'MinTemp', 'Temp3pm'],
                      labels={'value': 'Temperature (°C)', 'Date': 'Date'},
                      title=f'Temperature Trends in {location.upper()}')

        # Update layout for better visuals
        fig.update_layout(
            title={
                'text': f"Temperature Trends in {location.upper()}",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Date',
            yaxis_title='Temperature (°C)',
            legend_title_text='Temperature Types',
            template='plotly_white',
            hovermode='x'
        )

        graph_html = fig.to_html(full_html=False)
        return render_template('chart.html', graph_html=graph_html)
    else:
        return "Location not found"

# Rainfall distribution histogram route
@app.route('/rainfall_distribution')
def rainfall_distribution():
    location = request.args.get('location')
    data = df[df['Location'].str.contains(location, case=False, na=False)]

    if not data.empty:
        # Create a histogram for rainfall distribution
        fig = px.histogram(data, x='Rainfall', nbins=50,
                           title=f'Rainfall Distribution in {location.upper()}',
                           labels={'Rainfall': 'Daily Rainfall (mm)'})
        
        # Update layout for better visuals
        fig.update_layout(
            xaxis_title='Daily Rainfall (mm)',
            yaxis_title='Frequency',
            template='plotly_white'
        )

        graph_html = fig.to_html(full_html=False)
        return render_template('chart.html', graph_html=graph_html)
    else:
        return "Location not found"

# Correlation matrix route
@app.route('/correlation_matrix')
def correlation_matrix():
    location = request.args.get('location')
    data = df[df['Location'].str.contains(location, case=False, na=False)]

    if not data.empty:
        # Calculate the correlation matrix
        correlation_data = data[['MaxTemp', 'MinTemp', 'Temp3pm', 'Rainfall', 'Humidity3pm', 'Humidity9am']].corr()

        # Create a heatmap for the correlation matrix
        fig = px.imshow(correlation_data, text_auto=True, title=f'Correlation Matrix in {location.upper()}')
        
        # Update layout for better visuals
        fig.update_layout(
            xaxis_title='Climate Variables',
            yaxis_title='Climate Variables',
            template='plotly_white'
        )

        graph_html = fig.to_html(full_html=False)
        return render_template('chart.html', graph_html=graph_html)
    else:
        return "Location not found"

if __name__ == '__main__':
    app.run(debug=True)

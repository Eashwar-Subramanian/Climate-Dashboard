from flask import Flask, render_template, request, jsonify
import pandas as pd
import folium
from folium.plugins import TimestampedGeoJson, HeatMap
import plotly.express as px
from datetime import datetime
from pandas.tseries.offsets import DateOffset
import statsmodels.api as sm

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

# SARIMA forecasting function
def forecast_sarima(location_data):
    mintemp_model = sm.tsa.statespace.SARIMAX(location_data['MinTemp'], order=(1, 0, 1), seasonal_order=(1, 1, 0, 52))
    maxtemp_model = sm.tsa.statespace.SARIMAX(location_data['MaxTemp'], order=(1, 0, 1), seasonal_order=(1, 1, 1, 52))
    rainfall_model = sm.tsa.statespace.SARIMAX(location_data['Rainfall'], order=(0, 0, 0), seasonal_order=(1, 1, 1, 52))

    # Fit models
    mintemp_model_fit = mintemp_model.fit(disp=False)
    maxtemp_model_fit = maxtemp_model.fit(disp=False)
    rainfall_model_fit = rainfall_model.fit(disp=False)

    # Generate future dates (26 weeks from the last date in the data)
    future_dates = [location_data.index[-1] + DateOffset(weeks=x) for x in range(1, 27)]

    # Forecast the next 26 weeks for each variable
    mintemp_forecast = mintemp_model_fit.forecast(steps=26)
    maxtemp_forecast = maxtemp_model_fit.forecast(steps=26)
    rainfall_forecast = rainfall_model_fit.forecast(steps=26)

    # Create a DataFrame for the forecasts
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'MinTemp_Forecast': mintemp_forecast,
        'MaxTemp_Forecast': maxtemp_forecast,
        'Rainfall_Forecast': rainfall_forecast
    })
    forecast_df.set_index('Date', inplace=True)
    
    return forecast_df


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

# Forecast route
@app.route('/forecast', methods=['GET'])
def forecast():
    location = request.args.get('location')
    location_data = df[df['Location'].str.contains(location, case=False, na=False)]
    
    if not location_data.empty:
        # Convert the 'Date' column to datetime and set as index
        location_data['Date'] = pd.to_datetime(location_data['Date'])
        location_data.set_index('Date', inplace=True)

        # Resample and interpolate as per your original logic
        location_data = location_data.resample('W').mean().interpolate(method='linear')

        # Perform SARIMA forecasting
        forecast_df = forecast_sarima(location_data)

        # Convert forecast_df to JSON format for easy consumption
        forecast_json = forecast_df.reset_index().to_json(orient='records', date_format='iso')

        return jsonify(forecast_json)
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
                    'coordinates': [151.209900, -33.865143]  # Sydney
                },
                'properties': {
                    'time': '2023-09-29',
                    'location': 'Sydney'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [144.963058, -37.813629]  # Melbourne
                },
                'properties': {
                    'time': '2023-09-29',
                    'location': 'Melbourne'
                }
            },
            # Add more locations as needed
        ]
    }

    # Create a base map
    m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4)
    
    # Add timestamped geojson
    TimestampedGeoJson(data,
                        period='PT1M',
                        add_last_point=True).add_to(m)

    return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True)
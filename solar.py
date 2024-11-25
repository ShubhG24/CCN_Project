import pandas as pd
import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def call_solar_api(latitude, longitude, api_key, quality='HIGH'):
    url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
    params = {
        'location.latitude': latitude,
        'location.longitude': longitude,
        'requiredQuality': quality,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404 and quality == 'HIGH':
            print(f"No HIGH quality data found for ({latitude}, {longitude}), trying MEDIUM quality...")
            return None
        else:
            print(f"HTTP Error: {e}")
            return None
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def process_solar_data(input_file, api_key, output_directory="solar_data"):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Read the input CSV file
    df = pd.read_csv(input_file)

    # Add new columns for solar data
    df['NumPanels'] = None
    df['YearlyEnergy (kWh)'] = None
    df['SolarArea (m²)'] = None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for index, row in df.iterrows():
        print(f"\nProcessing location {index + 1}/{len(df)}")
        print(f"Site: {row['Name']}, Address: {row['Address']}")

        if pd.isna(row['Latitude']) or pd.isna(row['Longitude']):
            print(f"Skipping location due to missing coordinates")
            continue

        response = call_solar_api(row['Latitude'], row['Longitude'], api_key, 'HIGH')

        if response is None:
            response = call_solar_api(row['Latitude'], row['Longitude'], api_key, 'MEDIUM')

        if response is not None:
            try:
                solar_potential = response.get('solarPotential', {})
                panel_configs = solar_potential.get('solarPanelConfigs', [])

                if panel_configs:
                    max_config = panel_configs[-1]
                    df.at[index, 'NumPanels'] = max_config.get('panelsCount')
                    df.at[index, 'YearlyEnergy (kWh)'] = max_config.get('yearlyEnergyDcKwh')
                    df.at[index, 'SolarArea (m²)'] = solar_potential.get('maxArrayAreaMeters2')

                filename = f"solar_data_{row['Name'].replace(' ', '_')}_{index}_{timestamp}.json"
                filepath = os.path.join(output_directory, filename)
                with open(filepath, 'w') as f:
                    json.dump(response, f, indent=2)
                print(f"Saved detailed data to {filename}")

            except Exception as e:
                print(f"Error processing response: {e}")

        time.sleep(2)

    # Save updated CSV file
    output_csv = f"atlanta_solar_data_{timestamp}.csv"
    df.to_csv(output_csv, index=False)
    print(f"\nSaved updated data to {output_csv}")

def main():
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    INPUT_FILE = 'atlanta_waffle_houses.csv'

    try:
        print("Starting Solar API processing...")
        process_solar_data(INPUT_FILE, API_KEY)
        print("\nProcessing complete!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
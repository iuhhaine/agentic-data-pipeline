import json
import os
import requests
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from google.adk.agents import Agent

load_dotenv()


# 1. DATA INGESTION
def fetch_weather_data(latitude: float, longitude: float) -> dict:
    """Fetches hourly temperature forecast data from the Open-Meteo public API."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Failed to fetch weather data: {response.status_code}")


# 2. DATA PROCESSING
def process_weather_data(raw_data: dict) -> dict:
    """Filters the next 24 hours of temperature data and computes summary statistics."""
    hourly = raw_data.get("hourly", {})
    times = hourly.get("time", [])[:24]
    temps = hourly.get("temperature_2m", [])[:24]

    if not temps:
        raise ValueError("No temperature data found in raw API response.")

    return {
        "latitude": raw_data.get("latitude"),
        "longitude": raw_data.get("longitude"),
        "hours_analyzed": len(temps),
        "avg_temp_c": round(sum(temps) / len(temps), 2),
        "min_temp_c": min(temps),
        "max_temp_c": max(temps),
        "hourly_times": times,
        "hourly_temps": temps,
    }


# 3. CLOUD STORAGE
def upload_to_azure(processed_data: dict, filename: str = "processed_weather.json") -> str:
    """Uploads processed weather data as a JSON file to Azure Blob Storage."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "weather-data")

    if not connection_string:
        raise ValueError("Missing AZURE_STORAGE_CONNECTION_STRING in .env file.")

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)

    json_data = json.dumps(processed_data, indent=2)
    blob_client.upload_blob(json_data, overwrite=True)

    return f"Successfully uploaded {filename} to Azure container '{container_name}'."


# 4. VISUALIZATION
def generate_html_report(processed_data: dict, output_path: str = "report.html") -> str:
    """Generates an HTML dashboard with a summary table and interactive bar chart."""
    avg_t = processed_data["avg_temp_c"]
    min_t = processed_data["min_temp_c"]
    max_t = processed_data["max_temp_c"]
    times_json = json.dumps(processed_data["hourly_times"])
    temps_json = json.dumps(processed_data["hourly_temps"])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>24-Hour Weather Forecast Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 850px; margin: 40px auto; padding: 0 20px; color: #222; }}
        h1 {{ color: #1a73e8; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        th {{ background-color: #1a73e8; color: white; }}
    </style>
</head>
<body>
    <h1>24-Hour Weather Pipeline Report</h1>
    <p><strong>Coordinates:</strong> ({processed_data['latitude']}, {processed_data['longitude']})</p>

    <table>
        <tr>
            <th>Hours Analyzed</th>
            <th>Average Temp (°C)</th>
            <th>Minimum Temp (°C)</th>
            <th>Maximum Temp (°C)</th>
        </tr>
        <tr>
            <td>{processed_data['hours_analyzed']}</td>
            <td>{avg_t} °C</td>
            <td>{min_t} °C</td>
            <td>{max_t} °C</td>
        </tr>
    </table>

    <canvas id="tempChart" height="120"></canvas>
    <script>
        new Chart(document.getElementById('tempChart'), {{
            type: 'bar',
            data: {{
                labels: {times_json},
                datasets: [{{
                    label: 'Hourly Temperature (°C)',
                    data: {temps_json},
                    backgroundColor: 'rgba(26, 115, 232, 0.7)'
                }}]
            }}
        }});
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return f"HTML report successfully saved to {os.path.abspath(output_path)}"


# 5. AGENTIC ORCHESTRATOR (Google ADK)
root_agent = Agent(
    name="weather_pipeline_agent",
    model="gemini-3.5-flash-lite",
    description="Orchestrates an end-to-end weather data engineering pipeline.",
    instruction="""
    You are a data engineering assistant. When the user asks you to run the pipeline for a location:
    1. Call fetch_weather_data using the latitude and longitude (default to 39.1653, -86.5264 for Bloomington, IN if not provided).
    2. Pass the raw result to process_weather_data to calculate the 24-hour summary statistics.
    3. Pass the processed data to upload_to_azure to save 'processed_weather.json' in cloud storage.
    4. Pass the processed data to generate_html_report to create 'report.html'.
    Report back to the user once all 4 steps are complete.
    """,
    tools=[
        fetch_weather_data,
        process_weather_data,
        upload_to_azure,
        generate_html_report,
    ],
)
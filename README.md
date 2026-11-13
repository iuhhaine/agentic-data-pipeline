Used Azure Blob Storage for cloud object storage. I had issues creating accounts to get an API key in Google Console. 
report.html is for bloomington, IN coordinates. I used an API key from Google. 
# Agentic Weather Data Engineering Pipeline

An end-to-end agentic ETL pipeline built with **Google Agent Development Kit (ADK)**, **Open-Meteo API**, **Azure Blob Storage**, and **Chart.js**.

## Architecture
1. **Data Ingestion (`fetch_weather_data`):** Fetches hourly temperature forecast data from Open-Meteo.
2. **Processing (`process_weather_data`):** Filters the next 24 hours and computes average, minimum, and maximum temperatures.
3. **Cloud Storage (`upload_to_azure`):** Uploads the processed JSON dataset to Azure Blob Storage.
4. **Visualization (`generate_html_report`):** Produces `report.html` containing a summary table and interactive Chart.js bar chart.
5. **Agentic Orchestration (`root_agent`):** Uses Gemini via Google ADK to dynamically execute all four tools in sequence.

## Setup & Execution
1. Clone the repository and create a virtual environment:
   ```bash
   git clone <your-repo-url>
   cd agentic-data-pipeline
   python -m venv venv
   venv\Scripts\activate
a. Install the dependencies: pip install -r requirements.txt
b. create a .env file inside of weather_agent/ with your credentials: 
GOOGLE_API_KEY="your_gemini_api_key"
AZURE_STORAGE_CONNECTION_STRING="your_azure_connection_string"
AZURE_CONTAINER_NAME="weather-data"
c. run the agent: adk run weather_agent
d. type your command "example: run the weather data pipeline for New York, New York"
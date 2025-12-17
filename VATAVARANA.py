import streamlit as st
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
import os
import matplotlib.pyplot as plt

# --------------------------------
# Page Config
# --------------------------------
st.set_page_config(
    page_title="Bengaluru Weather Dashboard",
    page_icon="🌦️",
    layout="centered"
)

st.title("🌦️ Bengaluru Weather Dashboard (2014–2024)")

# --------------------------------
# File Name
# --------------------------------
CSV_FILE = "Bengaluru_Weather_2014_2024.csv"

# --------------------------------
# Fetch Weather Data (Open-Meteo)
# --------------------------------
@st.cache_data
def fetch_weather_data():
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": 12.9716,
        "longitude": 77.5937,
        "start_date": "2014-01-01",
        "end_date": "2024-12-31",
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "rain_sum",
            "wind_speed_10m_max"
        ],
        "timezone": "Asia/Kolkata"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()

    data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s"),
            end=pd.to_datetime(daily.TimeEnd(), unit="s"),
            freq="D",
            inclusive="left"
        ),
        "temp_max": daily.Variables(0).ValuesAsNumpy(),
        "temp_min": daily.Variables(1).ValuesAsNumpy(),
        "temp_mean": daily.Variables(2).ValuesAsNumpy(),
        "precipitation": daily.Variables(3).ValuesAsNumpy(),
        "rain": daily.Variables(4).ValuesAsNumpy(),
        "wind_speed_max": daily.Variables(5).ValuesAsNumpy()
    }

    df = pd.DataFrame(data)
    df.to_csv(CSV_FILE, index=False)
    return df

# --------------------------------
# Load Data
# --------------------------------
@st.cache_data
def load_data():
    if not os.path.exists(CSV_FILE):
        return fetch_weather_data()
    df = pd.read_csv(CSV_FILE)
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# --------------------------------
# User Inputs
# --------------------------------
year = st.selectbox("Select Year", sorted(df["year"].unique()))
month = st.selectbox(
    "Select Month",
    range(1, 13),
    format_func=lambda x: pd.to_datetime(str(x), format="%m").strftime("%B")
)

# --------------------------------
# Filter Data
# --------------------------------
filtered = df[(df["year"] == year) & (df["month"] == month)]

if filtered.empty:
    st.warning("No data available for selected month and year")
    st.stop()

# --------------------------------
# Calculations
# --------------------------------
total_rain = filtered["rain"].sum()
rainy_days = (filtered["rain"] > 0).sum()
avg_temp = filtered["temp_mean"].mean()
avg_max_temp = filtered["temp_max"].mean()

# --------------------------------
# Dominant Weather Logic
# --------------------------------
if total_rain > 0 and rainy_days >= 3:
    dominant_weather = "🌧️ Rain Dominant"
elif rainy_days == 0 and avg_max_temp >= 32:
    dominant_weather = "☀️ Heat Dominant"
else:
    dominant_weather = "🌤️ Mixed Weather"

# --------------------------------
# Rain Intensity Logic
# --------------------------------
if total_rain == 0:
    rain_intensity = "No Rain"
elif total_rain <= 50:
    rain_intensity = "Light Rain"
elif total_rain <= 150:
    rain_intensity = "Moderate Rain"
else:
    rain_intensity = "Heavy Rain"

# --------------------------------
# Display Metrics
# --------------------------------
st.subheader("📊 Monthly Weather Summary")

st.metric("Dominant Weather", dominant_weather)
st.metric("Average Temperature (°C)", f"{avg_temp:.2f}")
st.metric("Average Max Temperature (°C)", f"{avg_max_temp:.2f}")
st.metric("Total Rainfall (mm)", f"{total_rain:.2f}")
st.metric("Rainy Days", rainy_days)
st.metric("Rain Intensity", rain_intensity)

# --------------------------------
# 📈 Temperature Trend Graph
# --------------------------------
st.subheader("🌡️ Daily Temperature Trend")

fig, ax = plt.subplots()
ax.plot(filtered["date"], filtered["temp_max"], label="Max Temp")
ax.plot(filtered["date"], filtered["temp_mean"], label="Mean Temp")
ax.plot(filtered["date"], filtered["temp_min"], label="Min Temp")
ax.set_xlabel("Date")
ax.set_ylabel("Temperature (°C)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# --------------------------------
# 🌧️ Daily Rainfall Graph
# --------------------------------
st.subheader("🌧️ Daily Rainfall")

fig, ax = plt.subplots()
ax.bar(filtered["date"], filtered["rain"])
ax.set_xlabel("Date")
ax.set_ylabel("Rainfall (mm)")
ax.grid(True)
st.pyplot(fig)

# --------------------------------
# 📊 Rainy vs Dry Days Graph
# --------------------------------
st.subheader("📊 Rainy vs Dry Days")

rainy = (filtered["rain"] > 0).sum()
dry = (filtered["rain"] == 0).sum()

fig, ax = plt.subplots()
ax.bar(["Rainy Days", "Dry Days"], [rainy, dry])
ax.set_ylabel("Number of Days")
ax.grid(axis="y")
st.pyplot(fig)

# --------------------------------
# Optional Data Table
# --------------------------------
with st.expander("📅 Show Daily Weather Data"):
    st.dataframe(filtered)

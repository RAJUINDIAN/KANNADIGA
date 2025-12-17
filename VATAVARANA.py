import streamlit as st
import pandas as pd
import requests
import os

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
# CSV File
# --------------------------------
CSV_FILE = "Bengaluru_Weather_2014_2024.csv"

# --------------------------------
# Fetch Weather Data (Open-Meteo)
# --------------------------------
@st.cache_data
def fetch_weather_data():
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=12.9716"
        "&longitude=77.5946"
        "&start_date=2014-01-01"
        "&end_date=2024-12-31"
        "&daily=temperature_2m_max"
        ",temperature_2m_min"
        ",temperature_2m_mean"
        ",precipitation_sum"
        ",rain_sum"
        ",wind_speed_10m_max"
        "&timezone=Asia/Kolkata"
    )

    response = requests.get(url, timeout=30)
    data = response.json()

    df = pd.DataFrame({
        "date": pd.to_datetime(data["daily"]["time"]),
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "temp_mean": data["daily"]["temperature_2m_mean"],
        "precipitation": data["daily"]["precipitation_sum"],
        "rain": data["daily"]["rain_sum"],
        "wind_speed_max": data["daily"]["wind_speed_10m_max"]
    })

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
# 🌡️ Temperature Trend (Line Chart)
# --------------------------------
st.subheader("🌡️ Daily Temperature Trend")

temp_df = filtered.set_index("date")[[
    "temp_max", "temp_mean", "temp_min"
]]
st.line_chart(temp_df)

# --------------------------------
# 🌧️ Daily Rainfall (Bar Chart)
# --------------------------------
st.subheader("🌧️ Daily Rainfall")

rain_df = filtered.set_index("date")[["rain"]]
st.bar_chart(rain_df)

# --------------------------------
# 📊 Rainy vs Dry Days
# --------------------------------
st.subheader("📊 Rainy vs Dry Days")

summary_df = pd.DataFrame({
    "Days": ["Rainy Days", "Dry Days"],
    "Count": [
        (filtered["rain"] > 0).sum(),
        (filtered["rain"] == 0).sum()
    ]
}).set_index("Days")

st.bar_chart(summary_df)

# --------------------------------
# 📅 Data Table
# --------------------------------
with st.expander("📅 Show Daily Weather Data"):
    st.dataframe(filtered)


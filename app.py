import streamlit as st
import sys
from pathlib import Path

# Add src/ to path so we can import from load.py
sys.path.insert(0, str(Path(__file__).parent / "src"))

from load import query

# --- Page config ---
st.set_page_config(
    page_title="Weather + Energy Dashboard", page_icon="⚡", layout="wide"
)

st.title("⚡ Weather + Energy Demand Dashboard")
st.caption("Source: Open-Meteo API | Storage: DuckDB | Location: Manila, PH")


# --- Load data from DuckDB ---
@st.cache_data(ttl=300)  # Cache for 5 minutes to avoid re-querying on every interaction
def load_data():
    hourly = query("SELECT * FROM hourly_weather ORDER BY timestamp")
    daily = query("SELECT * FROM daily_summary ORDER BY date")
    return hourly, daily


try:
    hourly, daily = load_data()

    if hourly.empty:
        st.warning("No data yet. Run the pipeline first.")
        st.code("python src/pipeline.py")
        st.stop()

except Exception:
    st.error("Could not connect to the database.")
    st.info("Run the pipeline first:")
    st.code("python src/pipeline.py")
    st.stop()


# --- KPI Row ---
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Hours of Data", f"{len(hourly):,}")
col2.metric("Days Tracked", len(daily))
col3.metric("Avg Temperature", f"{hourly['temperature_c'].mean():.1f} °C")
col4.metric("Peak Energy Demand", f"{hourly['energy_demand_mw'].max():.0f} MW")

st.divider()

# --- Line Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Hourly Temperature (°C)")
    st.line_chart(hourly.set_index("timestamp")["temperature_c"], color="#3b82f6")

with col_right:
    st.subheader("Hourly Energy Demand (MW)")
    st.line_chart(hourly.set_index("timestamp")["energy_demand_mw"], color="#f97316")

# --- Daily comparison ---
st.subheader("Daily: Avg Temperature vs Avg Energy Demand")
chart_data = daily.set_index("date")[["avg_temp_c", "avg_energy_demand_mw"]]
st.line_chart(chart_data)

st.divider()

# --- Data tables ---
st.subheader("Daily Summary Table")
st.dataframe(daily, use_container_width=True, hide_index=True)

with st.expander("Raw Hourly Data (last 48 hours)"):
    st.dataframe(hourly.tail(48), use_container_width=True, hide_index=True)

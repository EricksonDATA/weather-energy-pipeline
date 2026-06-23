import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv
import plotly.graph_objects as go

# Load .env when running locally
load_dotenv()

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from load import query

# --- Page config ---
st.set_page_config(
    page_title="Weather + Energy Dashboard", page_icon="⚡", layout="wide"
)

st.title("⚡ Weather + Energy Demand Dashboard")
st.caption(
    "Source: Open-Meteo API | Storage: Supabase PostgreSQL | Location: Manila, PH"
)


# --- Load data ---
@st.cache_data(ttl=3600)
def load_data():
    hourly = query("SELECT * FROM hourly_weather ORDER BY timestamp")
    daily  = query("SELECT * FROM daily_summary ORDER BY date")
    return hourly, daily


try:
    hourly, daily = load_data()

    if hourly.empty:
        st.warning("No data yet. Run the pipeline first.")
        st.code("python src/pipeline.py")
        st.stop()

except Exception as e:
    st.error("Could not connect to the database.")
    st.code(str(e))
    st.stop()


# --- KPI Row ---
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Hours of Data",      f"{len(hourly):,}")
col2.metric("Days Tracked",       len(daily))
col3.metric("Avg Temperature",    f"{hourly['temperature_c'].mean():.1f} °C")
col4.metric("Peak Energy Demand", f"{hourly['energy_demand_mw'].max():.0f} MW")

st.divider()

# --- Hourly Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Hourly Temperature (°C)")
    st.line_chart(
        hourly.set_index("timestamp")["temperature_c"],
        color="#3b82f6"
    )

with col_right:
    st.subheader("Hourly Energy Demand (MW)")
    st.line_chart(
        hourly.set_index("timestamp")["energy_demand_mw"],
        color="#f97316"
    )

# --- Dual-axis chart ---
st.subheader("Daily: Avg Temperature vs Avg Energy Demand")
st.caption("Note: Energy demand is a modeled proxy based on temperature, not measured grid data.")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily["date"],
    y=daily["avg_temp_c"],
    name="Avg Temperature (°C)",
    line=dict(color="#3b82f6", width=2),
    yaxis="y1"
))

fig.add_trace(go.Scatter(
    x=daily["date"],
    y=daily["avg_energy_demand_mw"],
    name="Avg Energy Demand (MW)",
    line=dict(color="#f97316", width=2),
    yaxis="y2"
))

fig.update_layout(
    yaxis=dict(
        title="Temperature (°C)",
        side="left",
        color="#3b82f6",
        showgrid=False
    ),
    yaxis2=dict(
        title="Energy Demand (MW)",
        side="right",
        overlaying="y",
        color="#f97316",
        showgrid=False
    ),
    legend=dict(x=0, y=1.1, orientation="h"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=400,
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Tables ---
st.subheader("Daily Summary Table")
st.dataframe(daily, use_container_width=True, hide_index=True)

with st.expander("Raw Hourly Data (last 48 hours)"):
    st.dataframe(hourly.tail(48), use_container_width=True, hide_index=True)
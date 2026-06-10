import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Smart Home Dashboard", layout="wide")

st.title("🏠 Smart Home Monitoring Dashboard")

data = {
    "Time": ["10:00", "10:05", "10:10", "10:15", "10:20"],
    "Temperature": [28, 29, 31, 34, 33],
    "Humidity": [65, 66, 67, 70, 69],
    "Gas": [100, 130, 180, 260, 220],
    "Motion": ["No Motion", "No Motion", "Detected", "Detected", "No Motion"]
}

df = pd.DataFrame(data)
latest = df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Temperature", f"{latest['Temperature']} °C")
col2.metric("Humidity", f"{latest['Humidity']} %")
col3.metric("Gas Level", f"{latest['Gas']} ppm")
col4.metric("Motion", latest["Motion"])

st.subheader("📈 Temperature Chart")
fig1 = px.line(df, x="Time", y="Temperature", markers=True)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("📈 Gas Level Chart")
fig2 = px.line(df, x="Time", y="Gas", markers=True)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("🚨 Alert Monitoring")

if latest["Gas"] > 250:
    st.error("DANGER: High gas level detected!")
elif latest["Gas"] > 180:
    st.warning("WARNING: Gas level is increasing.")
else:
    st.success("Gas level is safe.")

if latest["Temperature"] > 32:
    st.warning("Temperature is high. Fan should be activated.")
else:
    st.success("Temperature is normal.")

if latest["Motion"] == "Detected":
    st.error("Motion detected! Possible intruder alert.")
else:
    st.success("No motion detected.")

st.subheader("📋 Sensor Data Table")
st.dataframe(df)
import streamlit as st
import requests
import pandas as pd

FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home.json"

st.set_page_config(
    page_title="Smart Home Dashboard",
    layout="wide"
)

st.title("🏠 Smart Home Energy Efficient Dashboard")

response = requests.get(FIREBASE_URL)

if response.status_code == 200:
    data = response.json()

    if data:
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("🌡 Temperature", f"{data.get('temperature', 0)} °C")
        col2.metric("💡 Light", data.get("light", 0))
        col3.metric("👥 People", data.get("people_count", 0))
        col4.metric("❄ AC Temp", data.get("ac_temp", "N/A"))

        st.subheader("System Status")
        st.write(f"Cooling Mode: {data.get('mode', 'Unknown')}")

        if data.get("people_count", 0) == 0:
            st.success("No motion detected.")
        else:
            st.info("Motion / occupancy detected.")

        st.subheader("📋 Sensor Data Table")
        df = pd.DataFrame([data])
        st.dataframe(df)

    else:
        st.warning("No data received yet.")

else:
    st.error("Unable to connect Firebase")
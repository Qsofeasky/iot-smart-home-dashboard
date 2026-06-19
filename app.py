import streamlit as st
import requests
import pandas as pd

FIREBASE_URL = "https://YOUR_PROJECT.firebaseio.com/smart_home.json"

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

        col1.metric(
            "🌡 Temperature",
            f"{data.get('temperature',0)} °C"
        )

        col2.metric(
            "💡 Light",
            data.get("light",0)
        )

        col3.metric(
            "👥 People",
            data.get("people_count",0)
        )

        col4.metric(
            "❄ AC Temp",
            data.get("ac_temp","N/A")
        )

        st.subheader("System Status")

        st.write(
            f"Cooling Mode: {data.get('mode','Unknown')}"
        )

else:
    st.error("Unable to connect Firebase")
else:
    st.success("No motion detected.")

st.subheader("📋 Sensor Data Table")
st.dataframe(df)

import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home_history.json"

st.set_page_config(page_title="Smart Home Dashboard", layout="wide")
st.title("🏠 Smart Home Energy Efficient Dashboard")

# Auto refresh every 10 seconds
st_autorefresh(interval=10000, key="data_refresh")

response = requests.get(FIREBASE_URL, headers={"Cache-Control": "no-cache"})

if response.status_code == 200:
    data = response.json()

    if data:
        df = pd.DataFrame(data).T.reset_index(drop=True)

        # Convert timestamp to readable time
        if "timestamp" in df.columns:
            df["time"] = pd.to_datetime(df["timestamp"], unit="s")
            df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        latest = df.iloc[-1]

        brightness = latest.get("brightness", latest.get("light", 0))
        brightness_level = latest.get("brightness_level", "Unknown")
        light_status = latest.get("light_status", "Unknown")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("🌡 Temperature", f"{latest.get('temperature', 0)} °C")
        col2.metric("💡 Brightness", f"{brightness} lux")
        col3.metric("🌗 Brightness Level", brightness_level)
        col4.metric("🚦 Light Status", light_status)
        col5.metric("👥 People", latest.get("people_count", 0))

        st.metric("❄ AC Temperature", f"{latest.get('ac_temp', 'N/A')} °C")

        st.subheader("System Status")
        st.write(f"Cooling Mode: {latest.get('mode', 'Unknown')}")

        if latest.get("people_count", 0) == 0:
            st.success("No motion detected.")
        else:
            st.info("Motion / occupancy detected.")

        st.subheader("🎥 Live Camera Feed")

        video_url = latest.get("video_stream_url", "")

        if video_url:
            st.warning(
                "If video does not show, it is because Streamlit Cloud cannot access raspberrypi.local. "
                "Use ngrok or Cloudflare Tunnel for the Raspberry Pi video stream."
            )

            st.components.v1.html(
                f"""
                <img src="{video_url}" width="700">
                """,
                height=500,
            )
        else:
            st.info("No video stream URL received yet.")

        st.subheader("📋 Sensor Data History")

        hide_cols = ["video_stream_url", "url", "timestamp"]

        display_df = df.drop(columns=[c for c in hide_cols if c in df.columns])

        preferred_cols = [
            "time",
            "temperature",
            "brightness",
            "brightness_level",
            "people_count",
            "light_status",
            "ac_temp",
            "mode"
        ]

        display_df = display_df[[c for c in preferred_cols if c in display_df.columns]]

        st.dataframe(display_df.tail(20), use_container_width=True)

        st.subheader("📊 Temperature Graph")

        if "temperature" in df.columns and "time" in df.columns:
            graph_df = df[["time", "temperature"]].copy()
            graph_df = graph_df.set_index("time")
            st.line_chart(graph_df)

        st.subheader("📊 Brightness Graph")

        if "brightness" in df.columns and "time" in df.columns:
            brightness_df = df[["time", "brightness"]].copy()
            brightness_df = brightness_df.set_index("time")
            st.line_chart(brightness_df)

    else:
        st.warning("No data received yet.")

else:
    st.error("Unable to connect Firebase")
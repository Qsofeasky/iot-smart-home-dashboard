import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home_history.json"

st.set_page_config(
    page_title="Smart Home Dashboard",
    page_icon="🏠",
    layout="wide"
)

st_autorefresh(interval=10000, key="data_refresh")

st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}

.big-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    color: #1f2937;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #6b7280;
    margin-bottom: 30px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    text-align: center;
}

.card h3 {
    color: #374151;
    font-size: 18px;
}

.card h1 {
    color: #2563eb;
    font-size: 32px;
}

.status-box {
    padding: 18px;
    border-radius: 15px;
    background: #ffffff;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>🏠 Smart Home Energy Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Real-time monitoring for temperature, brightness, occupancy, AC and light control</div>", unsafe_allow_html=True)

response = requests.get(FIREBASE_URL, headers={"Cache-Control": "no-cache"})

if response.status_code == 200:
    data = response.json()

    if data:
        df = pd.DataFrame(data).T.reset_index(drop=True)

        if "timestamp" in df.columns:
            df["time"] = pd.to_datetime(df["timestamp"], unit="s")
            df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        latest = df.iloc[-1]

        brightness = latest.get("brightness", latest.get("light", 0))
        brightness_level = latest.get("brightness_level", "Unknown")
        light_status = latest.get("light_status", "Unknown")
        people_count = latest.get("people_count", 0)
        temperature = latest.get("temperature", 0)
        ac_temp = latest.get("ac_temp", "N/A")

        st.markdown("### 📌 Live Sensor Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>🌡 Temperature</h3>
                <h1>{temperature} °C</h1>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card">
                <h3>💡 Brightness</h3>
                <h1>{brightness} lux</h1>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="card">
                <h3>🌗 Light Level</h3>
                <h1>{brightness_level}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="card">
                <h3>🚦 Light Status</h3>
                <h1>{light_status}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="card">
                <h3>👥 People</h3>
                <h1>{people_count}</h1>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        left, right = st.columns([1.2, 1])

        with left:
            st.markdown("### 📊 Sensor Graph Visualization")

            if "temperature" in df.columns and "time" in df.columns:
                temp_df = df[["time", "temperature"]].copy()
                temp_df = temp_df.set_index("time")
                st.line_chart(temp_df)

            if "brightness" in df.columns and "time" in df.columns:
                bright_df = df[["time", "brightness"]].copy()
                bright_df = bright_df.set_index("time")
                st.line_chart(bright_df)

            if "people_count" in df.columns and "time" in df.columns:
                people_df = df[["time", "people_count"]].copy()
                people_df = people_df.set_index("time")
                st.line_chart(people_df)

        with right:
            st.markdown("### 🧠 System Status")

            if people_count == 0:
                motion_status = "✅ No motion detected"
            else:
                motion_status = "⚠️ Motion / occupancy detected"

            st.markdown(f"""
            <div class="status-box">
                <h3>❄ AC Temperature</h3>
                <h1>{ac_temp} °C</h1>
                <p><b>Cooling Mode:</b> {latest.get("mode", "Unknown")}</p>
                <p><b>Motion Status:</b> {motion_status}</p>
                <p><b>Light Status:</b> {light_status}</p>
                <p><b>Brightness Condition:</b> {brightness_level}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🎥 Live Camera Feed")

            video_url = latest.get("video_stream_url", "")

            if video_url:
                st.components.v1.html(
                    f"""
                    <div style="background:white; padding:15px; border-radius:18px;
                    box-shadow:0px 4px 15px rgba(0,0,0,0.08); text-align:center;">
                        <img src="{video_url}" width="100%" style="border-radius:12px;">
                    </div>
                    """,
                    height=420,
                )
            else:
                st.info("No video stream URL received yet.")

        st.markdown("### 📋 Latest Sensor Data History")

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

    else:
        st.warning("No data received yet.")

else:
    st.error("Unable to connect Firebase")
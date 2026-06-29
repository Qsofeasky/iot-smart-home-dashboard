import streamlit as st
import requests
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home_history.json"

st.set_page_config(page_title="Smart Home Dashboard", page_icon="🏠", layout="wide")
st_autorefresh(interval=10000, key="data_refresh")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f8fafc, #e0f2fe);
    color: #111827;
}
.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 4px 16px rgba(0,0,0,0.08);
    text-align: center;
    border: 1px solid #e5e7eb;
}
.card h3 { color: #374151; font-size: 17px; }
.card h1 { color: #2563eb; font-size: 30px; }
.title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    color: #1e3a8a;
}
.subtitle {
    text-align: center;
    color: #475569;
    font-size: 18px;
    margin-bottom: 30px;
}
.status-box {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 4px 16px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🏠 Smart Home Energy Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Real-time temperature, brightness, occupancy and AI control prediction</div>", unsafe_allow_html=True)

response = requests.get(FIREBASE_URL + f"?t={int(time.time())}")

if response.status_code == 200:
    data = response.json()

    if data:
        df = pd.DataFrame(data).T.reset_index(drop=True)

        if "timestamp" in df.columns:
            df = df.sort_values(by="timestamp")
            df["time"] = pd.to_datetime(df["timestamp"], unit="s")
            df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        if "brightness" not in df.columns:
            df["brightness"] = df.get("light", 0)

        def get_brightness_level(value):
            try:
                value = float(value)
            except:
                value = 0

            if value < 300:
                return "DARK"
            elif value < 600:
                return "DIM"
            else:
                return "BRIGHT"

        df["brightness_level"] = df["brightness"].apply(get_brightness_level)

        if "light_status" in df.columns:
            df["light_numeric"] = df["light_status"].apply(
                lambda x: 1 if str(x).upper() == "ON" else 0
            )

        latest = df.iloc[-1]

        temperature = latest.get("temperature", 0)
        brightness = latest.get("brightness", 0)
        brightness_level = latest.get("brightness_level", "Unknown")
        people_count = latest.get("people_count", 0)
        light_status = latest.get("light_status", "Unknown")
        ac_temp = latest.get("ac_temp", "N/A")

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
                <h3>🌗 Brightness Level</h3>
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

        left, right = st.columns([1.3, 1])

        with left:
            st.markdown("### 📊 Temperature and Light Graph Over Time")

            if "temperature" in df.columns and "brightness" in df.columns and "time" in df.columns:
                sensor_graph = df[["time", "temperature", "brightness"]].copy()
                sensor_graph = sensor_graph.set_index("time")
                st.line_chart(sensor_graph)

            st.markdown("### 🤖 Prediction for Control Over Time")

            control_cols = []

            if "ac_temp" in df.columns:
                control_cols.append("ac_temp")

            if "light_numeric" in df.columns:
                control_cols.append("light_numeric")

            if control_cols and "time" in df.columns:
                control_graph = df[["time"] + control_cols].copy()
                control_graph = control_graph.set_index("time")
                st.line_chart(control_graph)

            st.caption("Note: Light prediction is shown as 1 = ON and 0 = OFF.")

        with right:
            st.markdown("### 🧠 Current System Status")

            if people_count == 0:
                motion_status = "✅ No motion detected"
            else:
                motion_status = "⚠️ Motion / occupancy detected"

            st.markdown(f"""
            <div class="status-box">
                <h2>❄ AC Prediction: {ac_temp} °C</h2>
                <p><b>Mode:</b> {latest.get("mode", "Unknown")}</p>
                <p><b>Motion:</b> {motion_status}</p>
                <p><b>Brightness:</b> {brightness} lux</p>
                <p><b>Brightness Condition:</b> {brightness_level}</p>
                <p><b>Light Prediction:</b> {light_status}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🎥 Live Camera Feed")

            video_url = str(latest.get("video_stream_url", "")).strip()

            if video_url:
                if not video_url.endswith("/video_feed"):
                    video_url = video_url.rstrip("/") + "/video_feed"

                st.markdown(f"[🔗 Open Camera Stream in New Tab]({video_url})")
                st.caption(f"Current video URL: {video_url}")

                st.components.v1.html(
                    f"""
                    <div style="background:white; padding:15px; border-radius:18px;
                    box-shadow:0px 4px 16px rgba(0,0,0,0.08); text-align:center;">
                        <img src="{video_url}" width="100%" style="border-radius:12px;">
                        <p style="font-size:13px; color:#64748b;">
                            If the video does not appear here, click the link above to open it in a new tab.
                        </p>
                    </div>
                    """,
                    height=460,
                )
            else:
                st.info("No video stream URL received yet.")

        st.markdown("### 📋 Sensor Data History")

        hide_cols = ["video_stream_url", "url", "timestamp", "light_numeric"]
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
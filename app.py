import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home_history.json"

st.set_page_config(page_title="Smart Home Dashboard", page_icon="🏠", layout="wide")
st_autorefresh(interval=10000, key="data_refresh")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef6ff 0%, #f8fafc 45%, #ecfeff 100%);
    color: #0f172a;
}
.block-container { padding-top: 2rem; }
.hero {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    padding: 30px;
    border-radius: 28px;
    color: white;
    text-align: center;
    box-shadow: 0 12px 30px rgba(37,99,235,0.25);
    margin-bottom: 25px;
}
.hero h1 { font-size: 46px; margin-bottom: 8px; }
.hero p { font-size: 18px; opacity: 0.95; }
.card {
    background: rgba(255,255,255,0.95);
    padding: 22px;
    border-radius: 22px;
    box-shadow: 0 8px 22px rgba(15,23,42,0.08);
    text-align: center;
    border: 1px solid #e2e8f0;
}
.card h3 { color: #475569; font-size: 16px; margin-bottom: 8px; }
.card h1 { color: #1d4ed8; font-size: 32px; margin: 0; }
.panel {
    background: rgba(255,255,255,0.96);
    padding: 24px;
    border-radius: 24px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    border: 1px solid #e2e8f0;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🏠 Smart Home Energy Dashboard</h1>
    <p>Real-time temperature, brightness, occupancy, AC prediction and light control</p>
</div>
""", unsafe_allow_html=True)

response = requests.get(FIREBASE_URL + f"?t={int(time.time())}")

if response.status_code == 200:
    data = response.json()

    if data:
        df = pd.DataFrame(data).T.reset_index(drop=True)

        if "timestamp" in df.columns:
            df = df.sort_values(by="timestamp")
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
            df["readable_time"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

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

        try:
            people_count_int = int(people_count)
        except:
            people_count_int = 0

        if people_count_int > 0:
            system_mode = "AI Control Active"
            mode_badge = "🟢 Active"
            motion_status = "⚠️ Motion / occupancy detected"
        else:
            system_mode = "Standby Mode"
            mode_badge = "⚪ Standby"
            motion_status = "✅ No motion detected"

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"<div class='card'><h3>🌡 Temperature</h3><h1>{temperature} °C</h1></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='card'><h3>💡 Brightness</h3><h1>{brightness} lux</h1></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='card'><h3>🌗 Light Level</h3><h1>{brightness_level}</h1></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='card'><h3>🚦 Light Status</h3><h1>{light_status}</h1></div>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div class='card'><h3>👥 People</h3><h1>{people_count_int}</h1></div>", unsafe_allow_html=True)

        st.write("")

        left, right = st.columns([1.45, 1])

        with left:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("### 🌡 Temperature Over Time")

            if "temperature" in df.columns and "readable_time" in df.columns:
                temp_fig = px.line(
                    df.tail(50),
                    x="readable_time",
                    y="temperature",
                    markers=True,
                    labels={"readable_time": "Time", "temperature": "Temperature (°C)"}
                )
                temp_fig.update_layout(template="plotly_white", height=340)
                st.plotly_chart(temp_fig, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("### 💡 Brightness Over Time")

            if "brightness" in df.columns and "readable_time" in df.columns:
                bright_fig = px.line(
                    df.tail(50),
                    x="readable_time",
                    y="brightness",
                    markers=True,
                    labels={"readable_time": "Time", "brightness": "Brightness (lux)"}
                )
                bright_fig.update_layout(template="plotly_white", height=340)
                st.plotly_chart(bright_fig, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("### 🤖 Prediction for Control Over Time")

            control_cols = []
            if "ac_temp" in df.columns:
                control_cols.append("ac_temp")
            if "light_numeric" in df.columns:
                control_cols.append("light_numeric")

            if control_cols and "readable_time" in df.columns:
                control_long = df.tail(50).melt(
                    id_vars="readable_time",
                    value_vars=control_cols,
                    var_name="Control Type",
                    value_name="Value"
                )

                control_fig = px.line(
                    control_long,
                    x="readable_time",
                    y="Value",
                    color="Control Type",
                    markers=True,
                    labels={"readable_time": "Time"}
                )
                control_fig.update_layout(template="plotly_white", height=340)
                st.plotly_chart(control_fig, use_container_width=True)

            st.caption("Light prediction: 1 = ON, 0 = OFF.")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown(f"""
            <div class="panel">
                <h3>🧠 Current System Status</h3>
                <h2>❄ AC Prediction: {ac_temp} °C</h2>
                <p><b>Mode:</b> {system_mode} {mode_badge}</p>
                <p><b>Motion:</b> {motion_status}</p>
                <p><b>Brightness:</b> {brightness} lux</p>
                <p><b>Brightness Condition:</b> {brightness_level}</p>
                <p><b>Light Prediction:</b> {light_status}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("### 🎥 Live Camera Feed")

            video_url = str(latest.get("video_stream_url", "")).strip()

            if video_url:
                if not video_url.endswith("/video_feed"):
                    video_url = video_url.rstrip("/") + "/video_feed"

                st.markdown(f"[🔗 Open Camera Stream in New Tab]({video_url})")

                st.components.v1.html(
                    f"""
                    <div style="background:white; padding:12px; border-radius:18px; text-align:center;">
                        <img src="{video_url}" width="100%" style="border-radius:14px;">
                        <p style="font-size:13px; color:#64748b;">
                            If video does not appear, open the stream in a new tab.
                        </p>
                    </div>
                    """,
                    height=430,
                )
            else:
                st.info("No video stream URL received yet.")

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### 📋 Latest Sensor Data History")

        hide_cols = ["video_stream_url", "url", "timestamp", "light_numeric", "datetime"]
        display_df = df.drop(columns=[c for c in hide_cols if c in df.columns])

        preferred_cols = [
            "readable_time",
            "temperature",
            "brightness",
            "brightness_level",
            "people_count",
            "light_status",
            "ac_temp",
            "mode"
        ]

        display_df = display_df[[c for c in preferred_cols if c in display_df.columns]]
        display_df = display_df.rename(columns={"readable_time": "time"})

        st.dataframe(display_df.tail(20), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("No data received yet.")

else:
    st.error("Unable to connect Firebase")
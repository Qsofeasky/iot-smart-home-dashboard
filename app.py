import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px


FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home_history.json"

st.set_page_config(page_title="Smart Home Dashboard", page_icon="🏠", layout="wide")


st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #edf6ff 0%, #f8fafc 45%, #ecfeff 100%);
    color: #0f172a;
}

.block-container { 
    padding-top: 1.5rem; 
}

.hero {
    background: linear-gradient(135deg, #1d4ed8, #06b6d4);
    padding: 32px;
    border-radius: 30px;
    color: white;
    text-align: center;
    box-shadow: 0 12px 30px rgba(37,99,235,0.25);
    margin-bottom: 25px;
}

.hero h1 { 
    font-size: 46px; 
    margin-bottom: 8px; 
}

.hero p { 
    font-size: 18px; 
    opacity: 0.95; 
}

.smart-home-box {
    background: rgba(255,255,255,0.96);
    padding: 24px;
    border-radius: 24px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    border: 1px solid #e2e8f0;
    margin-bottom: 20px;
}

.panel {
    background: transparent;
    padding: 10px 0px;
    border-radius: 0px;
    box-shadow: none;
    border: none;
    margin-bottom: 25px;
}

.panel-title {
    font-size: 24px;
    font-weight: 700;
    color: #1e3a8a;
    margin-bottom: 15px;
    border-bottom: 2px solid #dbeafe;
    padding-bottom: 10px;
}

.card {
    background: rgba(255,255,255,0.96);
    padding: 22px;
    border-radius: 22px;
    box-shadow: 0 8px 22px rgba(15,23,42,0.08);
    text-align: center;
    border: 1px solid #e2e8f0;
}

.card h3 { 
    color: #475569; 
    font-size: 16px; 
    margin-bottom: 8px; 
}

.card h1 { 
    color: #1d4ed8; 
    font-size: 30px; 
    margin: 0; 
}

.status-active {
    background: #dcfce7;
    color: #166534;
    padding: 8px 12px;
    border-radius: 999px;
    font-weight: 700;
}

.status-standby {
    background: #f1f5f9;
    color: #475569;
    padding: 8px 12px;
    border-radius: 999px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🏠 Smart Home Energy Dashboard</h1>
    <p>AI-powered monitoring for temperature, brightness, occupancy, AC prediction and light control</p>
</div>
""", unsafe_allow_html=True)

@st.fragment(run_every="10s")

def live_dashboard():

    response = requests.get(FIREBASE_URL + f"?t={int(time.time())}")

    if response.status_code == 200:
        data = response.json()

        if data:
            df = pd.DataFrame(data).T.reset_index(drop=True)

            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
                df = df.dropna(subset=["timestamp"])
                df = df.sort_values(by="timestamp")
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
                df["readable_time"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

            if "brightness" not in df.columns:
                df["brightness"] = df.get("light", 0)

            df["temperature"] = pd.to_numeric(df.get("temperature", 0), errors="coerce").fillna(0)
            df["brightness"] = pd.to_numeric(df.get("brightness", 0), errors="coerce").fillna(0)
            df["people_count"] = pd.to_numeric(df.get("people_count", 0), errors="coerce").fillna(0).astype(int)

            if "ac_temp" in df.columns:
                df["ac_temp"] = pd.to_numeric(df["ac_temp"], errors="coerce")

            def get_brightness_level(value):
                if value < 300:
                    return "DARK"
                elif value < 600:
                    return "DIM"
                else:
                    return "BRIGHT"

            # Brightness level
            df["brightness_level"] = df["brightness"].apply(get_brightness_level)

            # Occupancy
            df["occupancy_status"] = df["people_count"].apply(
                lambda x: "Occupied" if x > 0 else "Empty"
            )

            latest = df.iloc[-1]

            temperature = float(latest.get("temperature", 0))
            brightness = float(latest.get("brightness", 0))
            people_count = int(latest.get("people_count", 0))
            ac_temp = latest.get("ac_temp", "N/A")

            # Determine brightness level
            if brightness < 200:
                brightness_level = "DARK"
            elif brightness < 400:
                brightness_level = "DIM"
            else:
                brightness_level = "BRIGHT"

            # ---------- NEW LIGHT CONTROL LOGIC ----------
            if people_count == 0:
                light_status = "OFF"
            else:
                if brightness_level == "BRIGHT":
                    light_status = "OFF"
                else:
                    light_status = "ON"

            # Update dataframe so graphs and table use the new logic
            df.loc[df.index[-1], "light_status"] = light_status
            df.loc[df.index[-1], "brightness_level"] = brightness_level

            df["light_numeric"] = df["light_status"].apply(
                lambda x: 1 if str(x).upper() == "ON" else 0
)

            if people_count > 0:
                system_mode = "AI Control Active"
                mode_class = "status-active"
                mode_badge = "🟢 Active"
                motion_status = "Motion / occupancy detected"
            else:
                system_mode = "Standby Mode"
                mode_class = "status-standby"
                mode_badge = "⚪ Standby"
                motion_status = "No motion detected"

            if temperature < 24:
                comfort_status = "❄ Cold"
            elif temperature <= 28:
                comfort_status = "😊 Comfortable"
            else:
                comfort_status = "🔥 Hot"

            st.markdown("""
            <div class="smart-home-box">
                <div class="panel-title">🏡 Smart Home Application Overview</div>
                <p>
                This dashboard monitors a smart home environment using IoT sensors, YOLO-based human detection,
                and AI-driven energy management. The system automatically controls lighting and air conditioning
                based on occupancy, room temperature, and ambient brightness to improve energy efficiency.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.markdown(f"<div class='card'><h3>🌡 Temperature</h3><h1>{temperature:.1f} °C</h1></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='card'><h3>💡 Brightness</h3><h1>{brightness:.1f} lux</h1></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='card'><h3>🌗 Light Level</h3><h1>{brightness_level}</h1></div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div class='card'><h3>🚦 Light Status</h3><h1>{light_status}</h1></div>", unsafe_allow_html=True)
            with col5:
                st.markdown(f"<div class='card'><h3>👥 People</h3><h1>{people_count}</h1></div>", unsafe_allow_html=True)

            st.write("")

            left, right = st.columns([1.45, 1])

            with left:
                st.markdown("<div class='panel'>", unsafe_allow_html=True)
                st.markdown("<div class='panel-title'>🌡 Temperature Monitoring</div>", unsafe_allow_html=True)

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
                st.markdown("<div class='panel-title'>💡 Brightness Monitoring</div>", unsafe_allow_html=True)

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
                st.markdown("<div class='panel-title'>👥 Occupancy Monitoring</div>", unsafe_allow_html=True)

                people_fig = px.line(
                    df.tail(50),
                    x="readable_time",
                    y="people_count",
                    markers=True,
                    labels={"readable_time": "Time", "people_count": "People Count"}
                )
                people_fig.update_layout(template="plotly_white", height=340)
                st.plotly_chart(people_fig, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='panel'>", unsafe_allow_html=True)
                st.markdown("<div class='panel-title'>🤖 AI Energy Control Prediction</div>", unsafe_allow_html=True)

                control_cols = []
                if "ac_temp" in df.columns:
                    control_cols.append("ac_temp")
                if "light_numeric" in df.columns:
                    control_cols.append("light_numeric")

                if control_cols:
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
                    <div class="panel-title">🧠 Smart Home Status</div>
                    <p><span class="{mode_class}">{mode_badge}</span></p>
                    <h2>❄ AC Prediction: {ac_temp} °C</h2>
                    <p><b>Mode:</b> {system_mode}</p>
                    <p><b>Motion:</b> {motion_status}</p>
                    <p><b>People Detected:</b> {people_count}</p>
                    <p><b>Room Comfort:</b> {comfort_status}</p>
                    <p><b>Brightness:</b> {brightness:.1f} lux</p>
                    <p><b>Brightness Condition:</b> {brightness_level}</p>
                    <p><b>Light Prediction:</b> {light_status}</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div class='panel'>", unsafe_allow_html=True)
                st.markdown("<div class='panel-title'>🎥 Real-Time Camera Monitoring</div>", unsafe_allow_html=True)

                video_url = str(latest.get("video_stream_url", "")).strip()

                if video_url:
                    if not video_url.endswith("/video_feed"):
                        video_url = video_url.rstrip("/") + "/video_feed"

                    st.markdown(f"[🔗 Open Camera Stream in New Tab]({video_url})")

                    st.components.v1.html(
                        f"""
                        <div style="
                            background:white;
                            padding:12px;
                            border-radius:18px;
                            text-align:center;
                            height:500px;
                            overflow:hidden;
                        ">
                            <img src="{video_url}"
                                style="
                                    width:100%;
                                    height:450px;
                                    object-fit:cover;
                                    object-position:center;
                                    border-radius:14px;
                                ">
                            <p style="font-size:13px; color:#64748b;">
                                If video does not appear, open the stream in a new tab.
                            </p>
                        </div>
                        """,
                        height=530,
                    )
                else:
                    st.info("No video stream URL received yet.")

                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div class='panel'>", unsafe_allow_html=True)
                st.markdown("<div class='panel-title'>🏠 Room Occupancy Analysis</div>", unsafe_allow_html=True)

                occupancy_df = df["occupancy_status"].value_counts().reset_index()
                occupancy_df.columns = ["Status", "Count"]

                occ_fig = px.pie(
                    occupancy_df,
                    names="Status",
                    values="Count",
                    hole=0.45
                )
                occ_fig.update_layout(template="plotly_white", height=300)
                st.plotly_chart(occ_fig, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-title'>📋 Historical Sensor Records</div>", unsafe_allow_html=True)

            display_df = df.copy()

            hide_cols = [
                "video_stream_url",
                "url",
                "timestamp",
                "light_numeric",
                "datetime",
                "occupancy_status"
            ]

            display_df = display_df.drop(columns=[c for c in hide_cols if c in display_df.columns])

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

live_dashboard()
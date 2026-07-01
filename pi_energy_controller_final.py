import math
import os
import threading
import time
import urllib.request
from pathlib import Path

import adafruit_dht
import board
import cv2
import numpy as np
import requests
import RPi.GPIO as GPIO
import spidev

try:
    from flask import Flask, Response
except ImportError:
    Flask = None
    Response = None

from tree_models import predict_aircond, predict_light

# =============================================================
# DASHBOARD, CAMERA & HARDWARE CONFIGURATION
# =============================================================

# USB webcam is the default input. Set True only if using laptop camera server over WiFi.
USE_LAPTOP_CAMERA = False
LAPTOP_CAMERA_URL = "http://192.168.0.8:8080"

SEND_TO_FIREBASE = True
FIREBASE_URL = "https://smarthomeiot-574d7-default-rtdb.asia-southeast1.firebasedatabase.app/smart_home_history.json"

LIGHT_LED_PIN = 27  # GPIO 27 -- Physical Pin 13
DHT_DATA_PIN = board.D4  # GPIO 4 -- Physical Pin 7
MCP3008_CH = 0  # LDR connected to MCP3008 channel CH0
LOOP_INTERVAL = 10  # seconds between sensor/control updates

PERSON_CLASS_ID = 0
YOLO_IMG_SIZE = 320
YOLO_CONF_THRESHOLD = 0.5
YOLO_NMS_THRESHOLD = 0.45
YOLO_MODEL_PATH = Path(__file__).resolve().parent / "human_detection-main" / "yolov8n.onnx"
if not YOLO_MODEL_PATH.exists():
    YOLO_MODEL_PATH = Path.home() / "human_detection-main" / "yolov8n.onnx"
if not YOLO_MODEL_PATH.exists():
    YOLO_MODEL_PATH = Path.home() / "yolov8n.onnx"

VIDEO_STREAM_HOST = "0.0.0.0"
VIDEO_STREAM_PORT = 5000
VIDEO_STREAM_URL = os.getenv(
    "VIDEO_STREAM_URL",
    "https://YOUR-CLOUDFLARE-LINK.trycloudflare.com/video_feed",
)
SHOW_DETECTION_WINDOW = False  # Set True only on Pi desktop, False when using SSH.

# =============================================================
# INITIALIZATION
# =============================================================

GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_LED_PIN, GPIO.OUT)

dht_sensor = adafruit_dht.DHT11(DHT_DATA_PIN)

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

print(f"Loading YOLOv8 model: {YOLO_MODEL_PATH}")
human_net = cv2.dnn.readNetFromONNX(str(YOLO_MODEL_PATH))
human_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
human_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
print("YOLOv8 model loaded.")

cap = None
if USE_LAPTOP_CAMERA:
    print(f"Camera mode: laptop stream ({LAPTOP_CAMERA_URL})")
else:
    cap = cv2.VideoCapture(0)
    print(f"Camera mode: USB webcam | Opened: {cap.isOpened()}")

latest_lock = threading.Lock()
latest_people_count = 0
latest_detections = []
latest_frame_jpeg = None
camera_running = True

print("Tree models loaded from tree_models.py")

# =============================================================
# SENSOR FUNCTIONS
# =============================================================


def read_temperature():
    try:
        temp = dht_sensor.temperature
        if temp is not None:
            return float(temp)
    except RuntimeError:
        pass
    print("  [WARN] Temperature read failed, using default 28.0C")
    return 28.0


def read_brightness():
    try:
        result = spi.xfer2([1, (8 + MCP3008_CH) << 4, 0])
        adc_value = ((result[1] & 3) << 8) + result[2]
        brightness = (1 - adc_value / 1023.0) * 1000.0
        return round(brightness, 1)
    except Exception as e:
        print(f"  [WARN] Brightness read failed ({e}), using default 500 lux")
        return 500.0


def get_brightness_label(brightness):
    if brightness < 300:
        return "DARK"
    if brightness < 600:
        return "DIM"
    return "BRIGHT"


def get_frame():
    if USE_LAPTOP_CAMERA:
        try:
            data = urllib.request.urlopen(LAPTOP_CAMERA_URL, timeout=5).read()
            arr = np.frombuffer(data, np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"  [WARN] Laptop camera fetch failed ({e})")
            return None

    ret, frame = cap.read()
    if not ret:
        print("  [WARN] USB webcam read failed")
        return None
    return frame


# =============================================================
# HUMAN DETECTION + DASHBOARD VIDEO
# =============================================================


def letterbox(img, new_size, color=(114, 114, 114)):
    h, w = img.shape[:2]
    ratio = min(new_size / h, new_size / w)
    new_w, new_h = int(round(w * ratio)), int(round(h * ratio))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    canvas = np.full((new_size, new_size, 3), color, dtype=np.uint8)
    pad_x = (new_size - new_w) // 2
    pad_y = (new_size - new_h) // 2
    canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized
    return canvas, ratio, pad_x, pad_y


def detect_people(frame):
    letterboxed, ratio, pad_x, pad_y = letterbox(frame, YOLO_IMG_SIZE)
    blob = cv2.dnn.blobFromImage(
        letterboxed,
        scalefactor=1.0 / 255.0,
        size=(YOLO_IMG_SIZE, YOLO_IMG_SIZE),
        swapRB=True,
        crop=False,
    )
    human_net.setInput(blob)
    outputs = human_net.forward()

    preds = outputs[0].transpose()
    class_scores = preds[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(len(class_scores)), class_ids]

    mask = (class_ids == PERSON_CLASS_ID) & (confidences >= YOLO_CONF_THRESHOLD)
    preds = preds[mask]
    confidences = confidences[mask]

    boxes = []
    for cx, cy, w, h in preds[:, :4]:
        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        boxes.append([float(x1), float(y1), float(w), float(h)])

    detections = []
    if boxes:
        indices = cv2.dnn.NMSBoxes(
            boxes,
            confidences.tolist(),
            YOLO_CONF_THRESHOLD,
            YOLO_NMS_THRESHOLD,
        )
        if len(indices) > 0:
            for i in np.array(indices).flatten():
                x1, y1, w, h = boxes[i]
                x1 = (x1 - pad_x) / ratio
                y1 = (y1 - pad_y) / ratio
                w = w / ratio
                h = h / ratio
                detections.append((x1, y1, x1 + w, y1 + h, float(confidences[i])))

    return detections


def draw_detections(frame, detections, fps=0.0):
    for x1, y1, x2, y2, conf in detections:
        p1 = (int(x1), int(y1))
        p2 = (int(x2), int(y2))
        cv2.rectangle(frame, p1, p2, (0, 255, 0), 2)
        cv2.putText(
            frame,
            "person %.2f" % conf,
            (p1[0], max(p1[1] - 8, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    cv2.putText(
        frame,
        "FPS: %.1f  People: %d" % (fps, len(detections)),
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
    )
    return frame


def camera_detection_loop():
    global latest_people_count, latest_detections, latest_frame_jpeg, camera_running

    prev_time = time.time()
    fps_smooth = 0.0

    while camera_running:
        frame = get_frame()
        if frame is None:
            time.sleep(0.2)
            continue

        detections = detect_people(frame)

        now = time.time()
        inst_fps = 1.0 / max(now - prev_time, 1e-6)
        fps_smooth = inst_fps if fps_smooth == 0 else 0.9 * fps_smooth + 0.1 * inst_fps
        prev_time = now

        annotated = draw_detections(frame.copy(), detections, fps_smooth)
        ok, encoded = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        with latest_lock:
            latest_people_count = len(detections)
            latest_detections = detections
            if ok:
                latest_frame_jpeg = encoded.tobytes()

        if SHOW_DETECTION_WINDOW:
            cv2.imshow("Human Detection (press q to quit)", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                camera_running = False
                break


def get_latest_people_count():
    with latest_lock:
        return latest_people_count


def mjpeg_frames():
    while camera_running:
        with latest_lock:
            frame = latest_frame_jpeg

        if frame is None:
            time.sleep(0.1)
            continue

        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        time.sleep(0.03)


def start_video_stream_server():
    if Flask is None:
        print("  [WARN] Flask not installed. Run: pip install flask")
        print("  [WARN] Video stream server disabled.")
        return

    app = Flask(__name__)

    @app.route("/")
    def index():
        return (
            "<html><body>"
            "<h3>Smart Home Human Detection</h3>"
            "<img src='/video_feed' style='max-width:100%;'>"
            "</body></html>"
        )

    @app.route("/video_feed")
    def video_feed():
        return Response(mjpeg_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    thread = threading.Thread(
        target=lambda: app.run(
            host=VIDEO_STREAM_HOST,
            port=VIDEO_STREAM_PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        ),
        daemon=True,
    )
    thread.start()
    print(f"Local video server running on port {VIDEO_STREAM_PORT}")
    print(f"Dashboard video URL sent to Firebase: {VIDEO_STREAM_URL}")


# =============================================================
# MODEL, CONTROL & SYNC FUNCTIONS
# =============================================================


def adjust_aircond_for_people(base_aircond, people_count):
    if people_count <= 1:
        return round(base_aircond, 1)
    if people_count == 2:
        return round(base_aircond - 1.5, 1)
    return round(base_aircond - 3.0, 1)


def build_features(temp, brightness, occupancy):
    hour = time.localtime().tm_hour
    return {
        "temperature": temp,
        "brightness": brightness,
        "occupancy": occupancy,
        "hour_sin": math.sin(2 * math.pi * hour / 24),
        "hour_cos": math.cos(2 * math.pi * hour / 24),
    }


def control_led(light_on):
    GPIO.output(LIGHT_LED_PIN, GPIO.HIGH if light_on == 1 else GPIO.LOW)


def send_to_firebase(temp, brightness, bright_label, people_count, light_on, aircond_value):
    if not SEND_TO_FIREBASE:
        return

    payload = {
        "temperature": temp,
        "light": brightness,
        "brightness": brightness,
        "brightness_level": bright_label,
        "people_count": people_count,
        "occupancy": 1 if people_count > 0 else 0,
        "ac_temp": aircond_value,
        "aircond_value": aircond_value,
        "mode": "AI Control Active",
        "light_status": "ON" if light_on else "OFF",
        "video_stream_url": VIDEO_STREAM_URL,
        "timestamp": int(time.time()),
    }

    try:
        response = requests.post(FIREBASE_URL, json=payload, timeout=5)
        if response.status_code in (200, 201):
            print("  [Firebase] Data synced")
            print(f"  [Video] {VIDEO_STREAM_URL}")
        else:
            print(f"  [Firebase] Response {response.status_code}: {response.text[:80]}")
    except Exception as e:
        print(f"  [Firebase] Failed to sync: {e}")


# =============================================================
# MAIN LOOP
# =============================================================

print("\n" + "=" * 55)
print("  Smart Home Energy Control -- Running")
print(f"  Camera: {'laptop stream' if USE_LAPTOP_CAMERA else 'USB webcam on Pi'}")
print("  Press Ctrl+C to stop")
print("=" * 55)

camera_thread = threading.Thread(target=camera_detection_loop, daemon=True)
camera_thread.start()
start_video_stream_server()

try:
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Reading sensors...")

        temp = read_temperature()
        brightness = read_brightness()
        bright_label = get_brightness_label(brightness)
        people_count = get_latest_people_count()
        occupancy = 1 if people_count > 0 else 0

        features = build_features(temp, brightness, occupancy)
        light_pred = predict_light(features)
        aircond_base = round(predict_aircond(features), 1)
        aircond_final = adjust_aircond_for_people(aircond_base, people_count)

        control_led(light_pred)

        print(f"  Temp          : {temp}C")
        print(f"  Brightness    : {brightness} lux ({bright_label})")
        print(f"  People count  : {people_count} person{'s' if people_count != 1 else ''}")
        print(f"  -> Light      : {'ON  [LED is ON]' if light_pred else 'OFF [LED is OFF]'}")
        print(f"  -> Aircond    : {aircond_final}C", end="")
        if people_count >= 2:
            print(f" (adjusted from {aircond_base}C for {people_count} people)", end="")
        print()

        send_to_firebase(temp, brightness, bright_label, people_count, light_pred, aircond_final)

        print(f"  Next reading in {LOOP_INTERVAL} seconds...")
        time.sleep(LOOP_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    camera_running = False
    camera_thread.join(timeout=2)
    if cap:
        cap.release()
    spi.close()
    GPIO.cleanup()
    dht_sensor.exit()
    if SHOW_DETECTION_WINDOW:
        cv2.destroyAllWindows()
    print("Hardware cleaned up safely. Bye!")

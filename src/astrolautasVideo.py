import subprocess
import time
import threading
import os
import shutil
import serial
from datetime import datetime
from mpu6050 import mpu6050
import board
import busio
import adafruit_bmp280
from picamera import PiCamera
import math

# --- Configuration ---
VIDEO_DIR = "video"
LOG_DIR = "logs"
MIN_FREE_SPACE_MB = 500
VIDEO_SEGMENT_DURATION = 60  # seconds
VIDEO_TRIGGER_DELAY = 300  # seconds (5 minutes)
ACCELERATION_THRESHOLD = 15.0  # m/s^2, adjust as needed
stop_event = threading.Event()
video_triggered = threading.Event()
sensor_data_lock = threading.Lock()
sensor_snapshot = {}

# --- Create folders ---
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# --- Initialize sensors safely ---
sensor_mpu = None
sensor_bmp = None
sensor_mpu_available = False
sensor_bmp_available = False
camera_available = False

# MPU6050
try:
    sensor_mpu = mpu6050(0x68)
    sensor_mpu.get_accel_data()
    sensor_mpu_available = True
    print("[SENSOR] MPU6050 inicializado correctamente.")
except Exception as e:
    print(f"[SENSOR ERROR] MPU6050 no disponible: {e}")

# BMP280
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor_bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
    sensor_bmp.sea_level_pressure = 1013.25
    _ = sensor_bmp.pressure
    sensor_bmp_available = True
    print("[SENSOR] BMP280 inicializado correctamente.")
except Exception as e:
    print(f"[SENSOR ERROR] BMP280 no disponible: {e}")

# --- Generate log file with timestamp ---
log_filename = os.path.join(LOG_DIR, f"data_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.txt")

def log_sensor_data():
    start_time = time.time()
    try:
        with open(log_filename, "w") as log_file:
            while not stop_event.is_set():
                try:
                    acc = {"x": 0, "y": 0, "z": 0}
                    temp = 0.0
                    pres = 0.0
                    alt = 0.0

                    if sensor_mpu_available:
                        acc = sensor_mpu.get_accel_data()

                    if sensor_bmp_available:
                        temp = sensor_bmp.temperature
                        pres = sensor_bmp.pressure
                        alt = sensor_bmp.altitude

                    now = datetime.now().strftime("%H:%M:%S")

                    with sensor_data_lock:
                        sensor_snapshot.update({
                            "acc": acc,
                            "temp": round(temp, 2),
                            "pres": round(pres, 2),
                            "alt": round(alt, 2)
                        })

                    msg = f"{now} "
                    if sensor_mpu_available:
                        msg += f"A:{round(acc['x'], 2)},{round(acc['y'], 2)},{round(acc['z'], 2)} "
                    if sensor_bmp_available:
                        msg += f"T:{temp:.2f}C P:{pres:.2f}hPa ALT:{alt:.2f}m"

                    log_file.write(msg.strip() + "\n")
                    log_file.flush()
                    os.fsync(log_file.fileno())

                    # Condición 1: tiempo transcurrido
                    if not video_triggered.is_set() and (time.time() - start_time) > VIDEO_TRIGGER_DELAY:
                        print("[TRIGGER] Video iniciado por tiempo.")
                        video_triggered.set()

                    # Condición 2: aceleración alta
                    if sensor_mpu_available:
                        a_total = math.sqrt(acc['x']**2 + acc['y']**2 + acc['z']**2)
                        if not video_triggered.is_set() and a_total > ACCELERATION_THRESHOLD:
                            print(f"[TRIGGER] Video iniciado por aceleración: {a_total:.2f} m/s²")
                            video_triggered.set()

                    time.sleep(0.5)
                except Exception as e:
                    print(f"[LOG ERROR] {e}")
                    break
    except Exception as e:
        print(f"[FILE ERROR] {e}")

def send_radio():
    counter = 0
    try:
        with serial.Serial("/dev/serial0", 9600, timeout=1) as ser:
            time.sleep(2)
            while not stop_event.is_set():
                try:
                    with sensor_data_lock:
                        acc = sensor_snapshot.get("acc", {"x": 0, "y": 0, "z": 0})
                        temp = sensor_snapshot.get("temp", 0.0)
                        pres = sensor_snapshot.get("pres", 0.0)
                        alt = sensor_snapshot.get("alt", 0.0)

                    message = ""
                    if sensor_mpu_available:
                        message += (
                            f"A:{round(acc['x'],2)},{round(acc['y'],2)},{round(acc['z'],2)} "
                        )
                    if sensor_bmp_available:
                        message += (
                            f"T:{temp:.2f}C P:{pres:.2f}hPa ALT:{alt:.2f}m "
                        )
                    message += f"CNT:{counter}"

                    ser.write((message + "\n").encode("utf-8"))
                    print(f"[{counter}] UART -> Arduino: {message}")

                    counter += 1
                    time.sleep(1.0)

                except Exception as e:
                    print(f"[SERIAL ERROR] {e}")
                    break
    except Exception as e:
        print(f"[UART INIT ERROR] {e}")

def has_enough_space(path="/", required_mb=MIN_FREE_SPACE_MB):
    total, used, free = shutil.disk_usage(path)
    return free // (1024 * 1024) > required_mb

def record_video():
    global camera_available
    try:
        camera = PiCamera()
        camera.resolution = (1280, 720)
        camera.framerate = 30
        camera.shutter_speed = 10000
        camera.exposure_mode = "fixedfps"
        camera.awb_mode = "fluorescent"
        camera_available = True
        print("[VIDEO] Cámara inicializada correctamente.")

        video_triggered.wait()

        while not stop_event.is_set():
            if not has_enough_space():
                print("[VIDEO] Not enough space. Skipping this segment.")
                time.sleep(VIDEO_SEGMENT_DURATION)
                continue

            segment_name = datetime.now().strftime("%d_%m_%Y_%H%M%S")
            video_path = os.path.join(VIDEO_DIR, f"video_{segment_name}.h264")
            print(f"[VIDEO] Recording segment: {video_path}")

            try:
                camera.start_recording(video_path)
                start = time.time()
                while time.time() - start < VIDEO_SEGMENT_DURATION and not stop_event.is_set():
                    camera.wait_recording(1)
                camera.stop_recording()
            except Exception as segment_error:
                print(f"[VIDEO ERROR] During segment: {segment_error}")
                try:
                    camera.stop_recording()
                except:
                    pass

        camera.close()
        print("[VIDEO] Grabación finalizada.")
    except Exception as e:
        print(f"[VIDEO ERROR] Cámara no detectada o fallida: {e}")
        camera_available = False

# --- Main ---
if __name__ == "__main__":
    print("CanSat mission started.")

    t1 = threading.Thread(target=log_sensor_data)
    t2 = threading.Thread(target=send_radio)
    t3 = threading.Thread(target=record_video)

    t1.start()
    t2.start()
    t3.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down...")
        stop_event.set()

    t1.join()
    t2.join()
    t3.join()

    print("All threads stopped. Mission complete.")

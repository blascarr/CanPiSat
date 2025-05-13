import subprocess
import time
import threading
import os
import signal
import datetime
from mpu6050 import mpu6050
import board
import busio
import adafruit_bmp280
from picamera import PiCamera

# ==== CONFIGURACIÓN DE SENSORES Y RUTAS ====
CLIENT_EXECUTABLE_PATH = "/home/zms/CanPiSat/src/RadioHead-1.143/examples/raspi/rf69/base_rf69_client"
DATA_DIR = "data"
VIDEO_DIR = "video"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ==== FILTRO DE KALMAN SIMPLE ====
class KalmanFilter:
    def __init__(self, q=0.01, r=1.0):
        self.q = q
        self.r = r
        self.x = 0.0
        self.p = 1.0

    def update(self, measurement):
        self.p = self.p + self.q
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        return self.x

# ==== SENSOR SETUP ====
sensor_mpu = mpu6050(0x68)
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
bmp280.sea_level_pressure = 1013.25

# ==== VARIABLES COMPARTIDAS ====
accel_filtered = {'x': 0.0, 'y': 0.0, 'z': 0.0}
kalman_filters = {axis: KalmanFilter() for axis in ['x', 'y', 'z']}
stop_event = threading.Event()
contador = 0

# ==== FILENAMES ====
now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data_filename = os.path.join(DATA_DIR, f"data_{now_str}.log")
video_filename = os.path.join(VIDEO_DIR, f"video_{now_str}.mp4")

# ==== FUNCIONES ====
def sample_accelerometer():
    while not stop_event.is_set():
        acc = sensor_mpu.get_accel_data()
        for axis in ['x', 'y', 'z']:
            accel_filtered[axis] = kalman_filters[axis].update(acc[axis])
        time.sleep(0.05)

def send_messages():
    global contador
    with open(data_filename, 'w') as log:
        try:
            while not stop_event.is_set():
                temp = bmp280.temperature
                pres = bmp280.pressure
                alt = bmp280.altitude

                mensaje = (
                    f"A:{accel_filtered['x']:.2f},{accel_filtered['y']:.2f},{accel_filtered['z']:.2f} "
                    f"T:{temp:.2f}C P:{pres:.2f}hPa ALT:{alt:.2f}m CNT:{contador}"
                )

                print(f"Enviando: {mensaje}")
                log.write(mensaje + "\n")
                log.flush()
                subprocess.run([CLIENT_EXECUTABLE_PATH, mensaje])

                if "STOP" in mensaje:
                    stop_event.set()
                    break

                contador += 1
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[CTRL+C] Programa interrumpido")
            stop_event.set()

def record_video():
    camera = PiCamera()
    camera.resolution = (1280, 720)
    camera.framerate = 30
    camera.shutter_speed = 10000
    camera.exposure_mode = "fixedfps"
    camera.awb_mode = "fluorescent"
    temp_h264 = os.path.join(VIDEO_DIR, "temp_video.h264")

    print("[INFO] Iniciando grabación de video...")
    camera.start_recording(temp_h264)
    while not stop_event.is_set():
        camera.wait_recording(1)
    camera.stop_recording()
    camera.close()

    print("[INFO] Convirtiendo a MP4...")
    os.system(f"ffmpeg -y -i {temp_h264} -movflags +faststart -c:v copy {video_filename}")
    os.remove(temp_h264)
    print(f"[INFO] Video guardado: {video_filename}")

# ==== PROGRAMA PRINCIPAL ====
if __name__ == '__main__':
    accel_thread = threading.Thread(target=sample_accelerometer)
    send_thread = threading.Thread(target=send_messages)
    video_thread = threading.Thread(target=record_video)

    accel_thread.start()
    send_thread.start()
    video_thread.start()

    send_thread.join()
    stop_event.set()
    accel_thread.join()
    video_thread.join()

    print("[FIN] Todos los procesos han terminado.")

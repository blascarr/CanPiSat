import subprocess
import time
import threading
import os
from datetime import datetime

from mpu6050 import mpu6050
import board
import busio
import adafruit_bmp280
from picamera import PiCamera

# Configuración de rutas
CLIENT_EXECUTABLE_PATH = "/home/zms/CanPiSat/src/RadioHead-1.143/examples/raspi/rf69/base_rf69_client"
LOG_DIR = "/home/zms/CanPiSat/data"
VIDEO_DIR = "/home/zms/CanPiSat/videos"

# Crear carpetas si no existen
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# Timestamp para archivos únicos
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOG_DIR, f"telemetria_{timestamp}.txt")
video_filename = os.path.join(VIDEO_DIR, f"video_{timestamp}.h264")

# Inicializar sensores
sensor_mpu = mpu6050(0x68)
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
bmp280.sea_level_pressure = 1013.25  # hPa presión al nivel del mar

contador = 0
camera = PiCamera()

def send_messages():
    global contador
    try:
        with open(log_filename, "w") as logfile:
            while True:
                aceleracion = sensor_mpu.get_accel_data()
                temperature = bmp280.temperature
                pressure = bmp280.pressure
                altitude = bmp280.altitude

                acc_x = format(aceleracion['x'], '.2f')
                acc_y = format(aceleracion['y'], '.2f')
                acc_z = format(aceleracion['z'], '.2f')
                temp = format(temperature, '.2f')
                pres = format(pressure, '.2f')
                alt = format(altitude, '.2f')

                mensaje = (
                    f"A:{acc_x},{acc_y},{acc_z} "
                    f"T:{temp}C P:{pres}hPa ALT:{alt}m CNT:{contador}"
                )
                print(f"[{contador}] Enviando: {mensaje}")

                # Guardar en log
                logfile.write(f"{datetime.now().isoformat()} {mensaje}\n")
                logfile.flush()

                # Enviar por radio
                subprocess.run([CLIENT_EXECUTABLE_PATH, mensaje])

                contador += 1
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[🛑] Programa de envío interrumpido.")

def grabar_video():
    try:
        print("[🎥] Iniciando grabación de vídeo...")
        camera.start_recording(video_filename)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Grabación interrumpida.")
        camera.stop_recording()

if __name__ == '__main__':
    # Crear hilos
    send_thread = threading.Thread(target=send_messages)
    video_thread = threading.Thread(target=grabar_video)

    # Iniciar hilos
    send_thread.start()
    video_thread.start()

    # Esperar a que terminen
    send_thread.join()
    video_thread.join()

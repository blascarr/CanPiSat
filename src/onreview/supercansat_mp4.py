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

# Rutas
CLIENT_EXECUTABLE_PATH = "/home/zms/CanPiSat/src/RadioHead-1.143/examples/raspi/rf69/base_rf69_client"
SERVER_EXECUTABLE_PATH = "/home/zms/CanPiSat/src/RadioHead-1.143/examples/raspi/rf69/base_rf69_server"
LOG_DIR = "/home/zms/CanPiSat/data"
VIDEO_DIR = "/home/zms/CanPiSat/videos"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# Timestamp para nombre de archivos
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOG_DIR, f"telemetria_{timestamp}.txt")
video_filename = os.path.join(VIDEO_DIR, f"video_{timestamp}.h264")
final_video = os.path.join(VIDEO_DIR, f"video_{timestamp}.mp4")

# Inicializar sensores
sensor_mpu = mpu6050(0x68)
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
bmp280.sea_level_pressure = 1013.25

# Control de parada
stop_event = threading.Event()
camera = PiCamera()

def send_messages():
    contador = 0
    with open(log_filename, "w") as logfile:
        while not stop_event.is_set():
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

            logfile.write(f"{datetime.now().isoformat()} {mensaje}\n")
            logfile.flush()

            subprocess.run([CLIENT_EXECUTABLE_PATH, mensaje])
            contador += 1
            time.sleep(1)

def grabar_video():
    print("[🎥] Iniciando grabación de vídeo...")
    camera.resolution = (1280, 720)
    camera.framerate = 30
    camera.shutter_speed = 10000
    camera.exposure_mode = "fixedfps"
    camera.awb_mode = "fluorescent"
    camera.start_recording(video_filename)

    while not stop_event.is_set():
        time.sleep(1)

    camera.stop_recording()
    camera.close()
    print("[✅] Grabación finalizada.")

def listen_for_stop():
    print("[📡] Escuchando comandos...")
    with subprocess.Popen(SERVER_EXECUTABLE_PATH, stdout=subprocess.PIPE, text=True) as proc:
        for line in proc.stdout:
            print(f"[🛰️] Recibido: {line.strip()}")
            if "STOP" in line.upper():
                print("[⛔] Comando STOP recibido. Finalizando...")
                stop_event.set()
                break

def convertir_video():
    print("[🛠️] Convirtiendo vídeo a MP4...")
    os.system(f"ffmpeg -i {video_filename} -movflags +faststart -c:v copy {final_video}")
    os.remove(video_filename)
    print(f"[💾] Video guardado en: {final_video}")

# Programa principal
if __name__ == '__main__':
    try:
        threads = [
            threading.Thread(target=send_messages),
            threading.Thread(target=grabar_video),
            threading.Thread(target=listen_for_stop)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    except KeyboardInterrupt:
        print("\n[🔌] Interrupción manual detectada.")
        stop_event.set()

    convertir_video()
    print("[✔️] Programa finalizado correctamente.")

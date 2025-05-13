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

# --- Configuración global ---
EXECUTABLE = "/home/zms/CanPiSat/src/RadioHead-1.143/examples/raspi/rf69/base_rf69_client"
DURACION_SEGUNDOS = 3 * 60  # 15 minutos

# Inicializar sensores
sensor_mpu = mpu6050(0x68)
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
bmp280.sea_level_pressure = 1013.25

# Fecha y hora para nombres únicos
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/datos_{timestamp}.txt"
video_filename = f"video/video_{timestamp}"

# Crear carpetas si no existen
os.makedirs("logs", exist_ok=True)
os.makedirs("video", exist_ok=True)

# --- Variables compartidas ---
contador = 0
fin = threading.Event()

# --- Función de adquisición y envío ---
def adquirir_y_enviar():
    global contador
    with open(log_filename, "w") as log_file:
        while not fin.is_set():
            try:
                acc = sensor_mpu.get_accel_data()
                temp = bmp280.temperature
                pres = bmp280.pressure
                alt = bmp280.altitude

                acc_x = round(acc['x'], 2)
                acc_y = round(acc['y'], 2)
                acc_z = round(acc['z'], 2)
                mensaje = f"A:{acc_x},{acc_y},{acc_z} T:{round(temp, 2)}C P:{round(pres, 2)}hPa ALT:{round(alt, 2)}m CNT:{contador}"

                print(f"[{contador}] Enviando: {mensaje}")
                subprocess.run([EXECUTABLE, mensaje])
                log_file.write(mensaje + "\n")
                log_file.flush()

                contador += 1
                time.sleep(1)
            except Exception as e:
                print(f"Error en adquisición/envío: {e}")
                break

# --- Función de grabación de vídeo ---
def grabar_video():
    try:
        camera = PiCamera()
        camera.resolution = (1280, 720)
        camera.framerate = 30
        camera.shutter_speed = 10000
        camera.exposure_mode = "fixedfps"
        camera.awb_mode = "fluorescent"
        temp_file = "temp_video.h264"

        print("🎥 Iniciando grabación de video...")
        camera.start_recording(temp_file)
        start = time.time()

        while not fin.is_set() and (time.time() - start < DURACION_SEGUNDOS):
            camera.wait_recording(1)

        camera.stop_recording()
        camera.close()

        print("📼 Convirtiendo a MP4...")
        os.system(f"ffmpeg -y -i {temp_file} -movflags +faststart -c:v copy {video_filename}.mp4")
        os.remove(temp_file)
        print(f"✅ Video guardado como {video_filename}.mp4")

    except Exception as e:
        print(f"Error grabando video: {e}")

# --- Programa principal ---
if __name__ == "__main__":
    print("🚀 Iniciando adquisición y grabación por 15 minutos...")

    hilo_sensores = threading.Thread(target=adquirir_y_enviar)
    hilo_video = threading.Thread(target=grabar_video)

    hilo_sensores.start()
    hilo_video.start()

    # Esperar 15 minutos
    try:
        time.sleep(DURACION_SEGUNDOS)
    except KeyboardInterrupt:
        print("⛔ Interrumpido por el usuario.")

    fin.set()
    hilo_sensores.join()
    hilo_video.join()

    print("✅ Finalizado todo correctamente.")

import subprocess
import time
from mpu6050 import mpu6050
import board
import busio
import adafruit_bmp280

# Ruta a tu ejecutable C++
EXECUTABLE_PATH = "/home/zms/RadioHead-1.143/examples/raspi/rf69/base_rf69_client"

# Inicializar sensores
sensor_mpu = mpu6050(0x68)

i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
bmp280.sea_level_pressure = 1013.25  # presión al nivel del mar

contador = 0

try:
    while True:
        # Datos del giroscopio
        aceleracion = sensor_mpu.get_accel_data()
        giroscopio = sensor_mpu.get_gyro_data()

        # Datos del barómetro
        temperatura = bmp280.temperature
        presion = bmp280.pressure
        altitud = bmp280.altitude

        # Construimos el mensaje a enviar
        mensaje = f"A:{aceleracion} G:{giroscopio} T:{temperatura:.2f}C P:{presion:.2f}hPa ALT:{altitud:.2f}m CNT:{contador}"

        print(f"Enviando: {mensaje}")

        # Enviar usando rf69_client
        subprocess.run([EXECUTABLE_PATH, mensaje])

        contador += 1
        time.sleep(1)

except KeyboardInterrupt:
    print("\nPrograma interrumpido. Fin del test.")

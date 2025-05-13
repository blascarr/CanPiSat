import subprocess
import time
import threading
from mpu6050 import mpu6050
import board
import busio
import adafruit_bmp280

# Configuracion de rutas
CLIENT_EXECUTABLE_PATH = "/home/zms/CanPiSat/src/RadioHead-1.143/examples/raspi/rf69/base_rf69_client"

# Inicializar sensores
sensor_mpu = mpu6050(0x68)
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
bmp280.sea_level_pressure = 1013.25  # hPa presion al nivel del mar

contador = 0

# Funcion para enviar mensajes
def send_messages():
    global contador
    try:
        while True:
            aceleracion = sensor_mpu.get_accel_data()
            # giroscopio = sensor_mpu.get_gyro_data()
            temperature = bmp280.temperature
            pressure = bmp280.pressure
            altitude = bmp280.altitude

            acc_x = format(aceleracion['x'], '.2f')
            acc_y = format(aceleracion['y'], '.2f')
            acc_z = format(aceleracion['z'], '.2f')

            # gyro_x = round(giroscopio['x'], '.2f')
            # gyro_y = round(giroscopio['y'], '.2f')
            # gyro_z = round(giroscopio['z'], '.2f')

            temp = format(temperature, '.2f')
            pres = format(pressure, '.2f')
            alt = format(altitude, '.2f')

            # Formar mensaje
            mensaje = (
                f"A:{acc_x},{acc_y},{acc_z} "
                f"T:{temp}C P:{pres}hPa ALT:{alt}m CNT:{contador}"
            )
            print(f"Enviando: {mensaje}")

            # Ejecutar el programa C++ pasando el mensaje
            subprocess.run([CLIENT_EXECUTABLE_PATH, mensaje])

            contador += 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Programa de envio interrumpido.")

# Programa principal
if __name__ == '__main__':
    send_thread = threading.Thread(target=send_messages)
    send_thread.start()
    send_thread.join()

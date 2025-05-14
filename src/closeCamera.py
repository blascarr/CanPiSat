from picamera import PiCamera

try:
    cam = PiCamera()
    cam.close()
    print("Cámara cerrada correctamente.")
except Exception as e:
    print(f"Error al cerrar cámara: {e}")

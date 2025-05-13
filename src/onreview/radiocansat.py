import subprocess
import time
import threading

CLIENT_EXECUTABLE_PATH = "RadioHead-1.143/examples/raspi/rf69/base_rf69_client"
base_message = "TESTPYTHON"

counter = 0

def send_messages():
    global counter
    try:
        while True:
            message = f"{base_message} {counter}"
            print(f"Sending: {message}")
            subprocess.run([CLIENT_EXECUTABLE_PATH, message])
            counter += 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSending program interrupted. Ending test.")

def listen_messages():
    try:
        with subprocess.Popen(SERVER_EXECUTABLE_PATH, stdout=subprocess.PIPE, text=True) as proc:
            while True:
                output = proc.stdout.readline()
                if output:
                    print(f"Received: {output.strip()}")
                else:
                    break
    except KeyboardInterrupt:
        print("\nListening program interrupted. Ending test.")

if __name__ == '__main__':
    send_thread = threading.Thread(target=send_messages)

    send_thread.start()

    send_thread.join()


import serial
import requests

# COM Port
ser = serial.Serial('COM14', 115200)

server_url = "https://rfid-jyxq.onrender.com/rfid_auto"

print("Listening for RFID scans...")

while True:

    if ser.in_waiting:

        uid = ser.readline().decode().strip()

        print("Scanned UID:", uid)

        data = {
            "rfid": uid
        }

        try:

            response = requests.post(server_url, json=data)

            print("Server Response:", response.status_code)
            print(response.text)

        except Exception as e:

            print("Error:", e)
import serial
import requests
import json
import webbrowser

# COM PORT
ser = serial.Serial('COM14', 115200)

server_url = "https://rfid-jyxq.onrender.com/rfid_auto"

print("Listening for RFID scans...")

while True:

    if ser.in_waiting:

        try:

            raw_data = ser.readline().decode(errors='ignore').strip()

            # Print raw serial data
            print("RAW:", raw_data)

            # Only process JSON RFID data
            if not raw_data.startswith('{"rfid"'):
                continue

            # Convert JSON string to dictionary
            data = json.loads(raw_data)

            print("Valid RFID:", data)

            # Ignore logout clear signal
            if data["rfid"] == "CLEAR":
                print("Logout")
                continue

            # Send to Flask server
            response = requests.post(server_url, json=data)

            print("Server Response:", response.status_code)

            result = response.json()

            print(result)

            # Open dashboard automatically
            if "redirect" in result:

                dashboard_url = "https://rfid-jyxq.onrender.com/dashboard/doctor" + result["redirect"]

                print("Opening:", dashboard_url)

                webbrowser.open(dashboard_url)

            else:

                print("RFID not found in database")

        except Exception as e:

            print("Error:", e)
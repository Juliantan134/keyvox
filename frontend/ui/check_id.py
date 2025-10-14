# check_id.py
import serial.tools.list_ports

print("--- Searching for connected serial devices ---")
ports = serial.tools.list_ports.comports()

if not ports:
    print("No serial devices found.")
else:
    for port in ports:
        print(f"Device: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        print("-" * 30)

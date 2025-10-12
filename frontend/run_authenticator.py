import tkinter as tk
from tkinter import messagebox
import serial.tools.list_ports
import subprocess
import sys
import os
import secrets
import time

# --- CONFIGURATION ---
# The same settings from your main app
PICO_HWID = 'VID:PID=2E8A:0005'  # Use the ID for a running Pico
PICO_SECRET_KEY = b'keyvoxe66430a64b465138'
PYTHON_EXECUTABLE = sys.executable
APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
# --- CORE LOGIC ---
def verify_pico_token(port):
    """Performs a simple challenge-response with the Pico (non-HMAC)."""
    try:
        with serial.Serial(port, timeout=2) as ser:
            # 1. Create a simple, random challenge string
            challenge = secrets.token_hex(16)
            
            # 2. Send the challenge to the Pico
            ser.write(challenge.encode('utf-8') + b'\n')
            
            # 3. Read the Pico's response
            response = ser.readline().strip().decode('utf-8')
            
            # 4. Calculate what the response SHOULD be on our end
            #    We must convert our secret key from bytes to a string to combine them
            expected_response = PICO_SECRET_KEY.decode('utf-8') + challenge
            
            # 5. Compare the actual response to the expected one
            return response == expected_response
            
    except Exception as e:
        print(f"Verification failed: {e}")
        return False
    
def poll_for_pico(root, target_file):
    """Periodically checks if the Pico is connected."""
    print("🔄 Polling for Pico...")
    ports = serial.tools.list_ports.comports()
    pico_port = None
    
    for port in ports:
        if PICO_HWID in port.hwid:
            pico_port = port.device
            break

    if pico_port:
        print(f"✅ Pico detected on {pico_port}. Verifying...")
        time.sleep(1)
        if verify_pico_token(pico_port):
            print("✅ Hardware token verified! Launching main application...")
            
            # Close the hidden root window and the messagebox.
            root.destroy()
            
            # Launch the main app, passing the target file path.
            subprocess.Popen([PYTHON_EXECUTABLE, APP_PATH, target_file])
            
        else:
            messagebox.showerror("Error", "Invalid hardware token detected.")
            root.destroy() # Exit if an invalid token is found
    else:
        # If not found, check again in 1 second.
        root.after(1000, poll_for_pico, root, target_file)

if __name__ == "__main__":
    # Get the target file path passed by the .bat file.
    target_file_to_unlock = sys.argv[1] if len(sys.argv) > 1 else ""

    # 1. Create the main Tkinter window but KEEP IT HIDDEN.
    #    This is necessary for the messagebox and root.after() to work.
    root = tk.Tk()
    root.withdraw()

    # 2. Show the messagebox prompt to the user.
    messagebox.showinfo("Key Vox Authenticator", "Please insert your hardware token to continue.")

    # 3. Start polling for the Pico in the background.
    poll_for_pico(root, target_file_to_unlock)

    # 4. Start the Tkinter event loop to keep the script alive.
    root.mainloop()






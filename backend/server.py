import os
import sys
import json
import shutil
import hashlib
from datetime import datetime

# --- Third-Party Libraries ---
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from scipy.spatial.distance import cosine # Note: This will need to be changed later

# --- This allows the server to import from other local files ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Import our custom helpers ---
from helpers import get_voice_embedding
from config import VOICEPRINTS_DIR
# from extract_features import preprocess_and_extract_features, save_data_to_json

# ✅ FIX: The visualizer is temporarily disabled to allow the server to start.
# from visualizer import analyze_lstm_gates

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Global Path and Configuration Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB_PATH = os.path.join(BASE_DIR, 'users.json')
TEMP_AUDIO_DIR = os.path.join(BASE_DIR, 'temp_uploads')
RECORDINGS_DIR = os.path.join(BASE_DIR, 'recordings')

os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(VOICEPRINTS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# --- SECURITY THRESHOLD ---
# This is for Squared L2 distance, not Cosine. We'll fix the logic below.
SECURITY_THRESHOLD = 1.7012 

# --- User Data Helper Functions ---
def read_users():
    if not os.path.exists(USER_DB_PATH): return {}
    with open(USER_DB_PATH, 'r') as f:
        try: return json.load(f)
        except json.JSONDecodeError: return {}
def write_users(data):
    with open(USER_DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==============================================================================
# === API ENDPOINTS ===
# ==============================================================================

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok"})

# ... (Your register, enroll_voice, and check_enrollment endpoints remain the same) ...
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    users = read_users()
    username = data['username'].lower()
    if username in users:
        return jsonify({"status": "error", "message": "Username already exists."}), 409
    users[username] = {
        "full_name": data['full_name'], "email": data['email'],
        "password_hash": hash_password(data['password']), "voiceprint_path": None
    }
    write_users(users)
    return jsonify({"status": "success", "message": "User registered. Proceed to voice enrollment."})

@app.route('/api/enroll_voice', methods=['POST'])
def enroll_voice():
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    users = read_users()
    if username not in users:
        return jsonify({"status": "error", "message": "User not found."}), 404
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"enroll_{username}.wav")
    audio_file.save(temp_filepath)
    try:
        voice_embedding = get_voice_embedding(temp_filepath)
        if voice_embedding is None:
            return jsonify({"status": "error", "message": "Could not process audio."}), 400
        voiceprint_filename = f"{username}.npy"
        absolute_voiceprint_path = os.path.join(VOICEPRINTS_DIR, voiceprint_filename)
        np.save(absolute_voiceprint_path, voice_embedding)
        users[username]['voiceprint_path'] = os.path.join("voiceprints", voiceprint_filename).replace("\\", "/")
        write_users(users)
        return jsonify({"status": "success", "message": "Voice enrolled."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Enrollment failed: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@app.route('/api/check_enrollment', methods=['POST'])
def check_enrollment():
    username = request.get_json()['username'].lower()
    user = read_users().get(username)
    if user and user.get('voiceprint_path'):
        voiceprint_path = os.path.join(BASE_DIR, user['voiceprint_path'])
        if os.path.exists(voiceprint_path):
            return jsonify({"enrolled": True})
    return jsonify({"enrolled": False})

@app.route('/api/verify_voice', methods=['POST'])
def verify_voice():
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    user = read_users().get(username)
    
    if not user or not user.get('voiceprint_path'):
        return jsonify({"verified": False, "message": "User or voiceprint not found."})
    
    stored_voiceprint_path = os.path.join(BASE_DIR, user['voiceprint_path'])
    if not os.path.exists(stored_voiceprint_path):
        return jsonify({"verified": False, "message": "Stored voiceprint file is missing."})
        
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, f"verify_{username}.wav")
    try:
        audio_file.save(temp_filepath)
        print(f"--- [VERIFY CHECK 1] Running Speaker Verification for {username} ---")
        live_embedding = get_voice_embedding(temp_filepath)
        if live_embedding is None:
            return jsonify({"verified": False, "message": "Could not process live audio."})

        stored_embedding = np.load(stored_voiceprint_path)
        
        # ✅ CRITICAL FIX: Use Squared L2 Distance to match the threshold
        distance = np.sum(np.square(stored_embedding - live_embedding))
        
        print(f"Voice similarity distance (Squared L2): {distance:.4f} (Threshold: < {SECURITY_THRESHOLD})")
        
        if distance < SECURITY_THRESHOLD:
            print("--- Verification successful ---")
            return jsonify({"verified": True})
        else:
            print("--- Verification failed: Voice does not match ---")
            return jsonify({"verified": False, "message": "Voice does not match."})
            
    except Exception as e:
        # This is where the model loading error will now appear
        print(f"AN ERROR OCCURRED DURING VERIFICATION: {e}")
        return jsonify({"verified": False, "message": f"An unexpected error occurred: {str(e)}"})
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data['username'].lower(), data['password']
    user = read_users().get(username)
    if user and user['password_hash'] == hash_password(password):
        user_details = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify({"login_success": True, "user_details": user_details})
    return jsonify({"login_success": False, "message": "Invalid credentials."})

# ✅ FIX: Temporarily disable the visualizer endpoint
# @app.route('/api/visualize_gates', methods=['POST'])
# def visualize_gates():
#    # ... implementation ...

# --- Main Execution Block ---
if __name__ == '__main__':
    from waitress import serve
    print("--- Starting production-ready server on http://127.0.0.1:5000 ---")
    serve(app, host="127.0.0.1", port=5000)
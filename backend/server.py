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
# REMOVED: from scipy.spatial.distance import cosine (no longer needed)
# COMMENTED OUT: import speech_recognition as sr
# COMMENTED OUT: import noisereduce as nr
import soundfile as sf

# --- This allows the server to import from other local files ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Import our custom helpers ---
from helpers import get_voice_embedding
from config import VOICEPRINTS_DIR
# Assuming these exist and work, adjust imports if needed
from extract_features import preprocess_and_extract_features, save_data_to_json
from visualizer import analyze_lstm_gates

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Global Path and Configuration Setup ---
ROOT_DIR = os.path.dirname(__file__)
USER_DB_PATH = os.path.join(ROOT_DIR, 'users.json')
TEMP_AUDIO_DIR = os.path.join(ROOT_DIR, 'temp_uploads')
RECORDINGS_DIR = os.path.join(ROOT_DIR, 'recordings')
# Make sure VOICEPRINTS_DIR from config is absolute or resolved correctly
if not os.path.isabs(VOICEPRINTS_DIR):
    VOICEPRINTS_DIR = os.path.join(ROOT_DIR, VOICEPRINTS_DIR)

os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(VOICEPRINTS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# --- SECURITY THRESHOLD ---
# Using the threshold from RAW Cosine Score (Best Accuracy point)
SECURITY_THRESHOLD = 0.989
# COMMENTED OUT: Accepted Passphrases list is no longer needed
# ACCEPTED_PASSPHRASES = [ ... ]

# --- User Data Helper Functions ---
# (read_users, write_users, hash_password, resolve_voiceprint_path remain the same)
def read_users():
    if not os.path.exists(USER_DB_PATH): return {}
    try:
        if os.path.getsize(USER_DB_PATH) > 0:
            with open(USER_DB_PATH, 'r') as f:
                return json.load(f)
        else:
            return {}
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Warning: Could not read or decode {USER_DB_PATH}. Returning empty user data.")
        return {}
    except Exception as e:
        print(f"Unexpected error reading user data: {e}")
        return {}
def write_users(data):
    try:
        with open(USER_DB_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error writing user data to {USER_DB_PATH}: {e}")
    except Exception as e:
         print(f"Unexpected error writing user data: {e}")
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def resolve_voiceprint_path(path):
    if not path: return None
    if os.path.isabs(path): return path
    filename = os.path.basename(path)
    return os.path.join(VOICEPRINTS_DIR, filename)

# ====================================================================
# === API ENDPOINTS
# ====================================================================

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok"})

@app.route('/api/register', methods=['POST'])
# (register endpoint remains the same)
def register():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
             return jsonify({"status": "error", "message": "Missing username or password."}), 400
        users = read_users()
        username = data['username'].lower()
        if not username:
             return jsonify({"status": "error", "message": "Username cannot be empty."}), 400
        if username in users:
            return jsonify({"status": "error", "message": "Username already exists."}), 409
        users[username] = {
            "full_name": data.get('full_name', ''),
            "email": data.get('email', ''),
            "password_hash": hash_password(data['password']),
            "voiceprint_path": None
        }
        write_users(users)
        return jsonify({"status": "success", "message": "User registered. Proceed to voice enrollment."})
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"status": "error", "message": "Registration failed due to server error."}), 500

@app.route('/api/enroll_voice', methods=['POST'])
# (enroll_voice endpoint remains the same)
def enroll_voice():
    if 'username' not in request.form or 'audio_file' not in request.files:
         return jsonify({"status": "error", "message": "Missing username or audio file."}), 400
    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    users = read_users()
    if username not in users:
        return jsonify({"status": "error", "message": "User not found."}), 404
    timestamp_short = datetime.now().strftime('%Y%m%d%H%M%S%f')
    temp_filename = f"enroll_{username}_{timestamp_short}.wav"
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, temp_filename)
    try:
        audio_file.save(temp_filepath)
        voice_embedding = get_voice_embedding(temp_filepath)
        if voice_embedding is None:
            return jsonify({"status": "error", "message": "Could not process audio file. It might be too short or silent."}), 400
        voice_embedding = np.asarray(voice_embedding, dtype=np.float32)
        norm = np.linalg.norm(voice_embedding)
        if norm < 1e-6:
             print(f"Warning: Near-zero norm for enrollment embedding for {username}.")
             return jsonify({"status": "error", "message": "Processed audio resulted in a near-zero embedding. Please record again clearly."}), 400
        voice_embedding = voice_embedding / norm
        voiceprint_filename = f"{username}.npy"
        absolute_voiceprint_path = os.path.join(VOICEPRINTS_DIR, voiceprint_filename)
        np.save(absolute_voiceprint_path, voice_embedding)
        users[username]['voiceprint_path'] = voiceprint_filename
        write_users(users)
        perm_filename = f"{username}_enroll_{timestamp_short}.wav"
        permanent_audio_path = os.path.join(RECORDINGS_DIR, perm_filename)
        try: shutil.copy(temp_filepath, permanent_audio_path)
        except Exception as copy_e: print(f"Warning: Could not save permanent recording copy: {copy_e}")
        return jsonify({"status": "success", "message": "Voice enrolled successfully."})
    except Exception as e:
        print(f"Error during voice enrollment for {username}: {e}")
        return jsonify({"status": "error", "message": f"Enrollment failed due to a server error."}), 500
    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            try: os.remove(temp_filepath)
            except OSError as e: print(f"Error removing temp file {temp_filepath}: {e}")

@app.route('/api/check_enrollment', methods=['POST'])
# (check_enrollment endpoint remains the same)
def check_enrollment():
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({"enrolled": False, "message": "Missing username."}), 400
        username = data['username'].lower()
        user = read_users().get(username)
        if user and user.get('voiceprint_path'):
            voiceprint_filename = user['voiceprint_path']
            absolute_voiceprint_path = os.path.join(VOICEPRINTS_DIR, voiceprint_filename)
            if os.path.exists(absolute_voiceprint_path):
                return jsonify({"enrolled": True})
        return jsonify({"enrolled": False})
    except Exception as e:
        print(f"Error checking enrollment: {e}")
        return jsonify({"enrolled": False, "message": "Error checking enrollment status."}), 500

@app.route('/api/verify_voice', methods=['POST'])
def verify_voice():
    if 'username' not in request.form or 'audio_file' not in request.files:
         return jsonify({"verified": False, "message": "Missing username or audio file."}), 400

    username = request.form['username'].lower()
    audio_file = request.files['audio_file']
    user = read_users().get(username)

    temp_filepath = None
    # COMMENTED OUT: cleaned_filepath no longer needed unless uncommenting NR/SR
    cleaned_filepath = None # Keep variable defined even if commented out below

    if not user or not user.get('voiceprint_path'):
        print(f"Verification attempt failed: User '{username}' not found or not enrolled.")
        return jsonify({"verified": False, "message": "User not found or voice not enrolled."}), 404

    voiceprint_filename = user['voiceprint_path']
    stored_voiceprint_path = os.path.join(VOICEPRINTS_DIR, voiceprint_filename)

    if not os.path.exists(stored_voiceprint_path):
        print(f"Verification FAILED for {username}: Stored voiceprint file missing at {stored_voiceprint_path}")
        return jsonify({"verified": False, "message": "Stored voiceprint file is missing. Please re-enroll."}), 500

    timestamp_short = datetime.now().strftime('%Y%m%d%H%M%S%f')
    temp_filename = f"verify_{username}_{timestamp_short}.wav"
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, temp_filename)

    try:
        audio_file.save(temp_filepath)

        # --- NEW: Check for Silence/Low Energy ---
        try:
            audio_data, sample_rate = sf.read(temp_filepath)
            # Ensure mono
            if audio_data.ndim > 1 and audio_data.shape[1] > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Calculate Root Mean Square (RMS) energy
            rms = np.sqrt(np.mean(audio_data**2))
            print(f"Live audio RMS energy for {username}: {rms:.6f}")

            # Define a minimum energy threshold (<<< ADJUST BASED ON TESTING >>>)
            MIN_RMS_THRESHOLD = 0.020 # Example: Start tuning here

            if rms < MIN_RMS_THRESHOLD:
                print(f"Verification FAILED for {username}: Live audio below RMS energy threshold ({rms:.6f} < {MIN_RMS_THRESHOLD}).")
                # Optionally, add duration check here too if needed
                return jsonify({"verified": False, "message": "Audio recording too quiet or silent. Please speak clearly."}), 400
            else:
                 print(f"Live audio RMS energy OK for {username}.")


        except Exception as energy_e:
            print(f"Error checking audio energy for {username}: {energy_e}")
            # Fail verification if energy check fails
            return jsonify({"verified": False, "message": "Error analyzing audio energy."}), 500
        # --- End NEW Check ---


        # --- Voice Verification (Proceed only if energy check passes) ---
        print(f"--- [VERIFY CHECK] Running Speaker Verification for {username} ---")
        live_embedding = get_voice_embedding(temp_filepath)
        if live_embedding is None:
            print(f"Verification FAILED for {username}: Could not process live audio.")
            return jsonify({"verified": False, "message": "Could not process live audio for speaker verification."}), 400

        # Ensure numpy array and normalize live embedding
        live_embedding = np.asarray(live_embedding, dtype=np.float32)
        le_norm = np.linalg.norm(live_embedding)
        if le_norm < 1e-6:
             print(f"Verification FAILED for {username}: Live embedding norm is near zero.")
             return jsonify({"verified": False, "message": "Live audio resulted in a near-zero embedding. Please record clearly."}), 400
        live_embedding = live_embedding / le_norm

        # Load and normalize stored embedding
        stored_embedding = np.load(stored_voiceprint_path)
        stored_embedding = np.asarray(stored_embedding, dtype=np.float32)
        se_norm = np.linalg.norm(stored_embedding)
        if se_norm < 1e-6:
             print(f"Error: Stored embedding norm is near zero for {username}. User may need to re-enroll.")
             return jsonify({"verified": False, "message": "Stored voiceprint is invalid. Please re-enroll."}), 500
        stored_embedding = stored_embedding / se_norm

        # Basic sanity checks
        if np.any(np.isnan(live_embedding)) or np.any(np.isnan(stored_embedding)):
             print(f"Error: NaN found in embeddings for {username}.")
             return jsonify({"verified": False, "message": "Embedding calculation error (NaN)."}), 500
        if live_embedding.shape != stored_embedding.shape:
             print(f"Error: Embedding shape mismatch for {username}. Stored: {stored_embedding.shape}, Live: {live_embedding.shape}")
             return jsonify({"verified": False, "message": "Embedding shape mismatch error."}), 500

        # Calculate Cosine SIMILARITY
        similarity = np.dot(stored_embedding, live_embedding)
        similarity = np.clip(similarity, -1.0, 1.0)

        print(f"Voice similarity score for {username}: {similarity:.4f} (Threshold: > {SECURITY_THRESHOLD})")

        # Compare SIMILARITY
        if similarity < SECURITY_THRESHOLD:
            print(f"--- Verification FAILED for {username}: Voice mismatch (Score {similarity:.4f} < {SECURITY_THRESHOLD}) ---")
            return jsonify({"verified": False, "message": "Voice does not match."})
        else:
            # ✅ If voice matches, VERIFY SUCCEEDS immediately (since passphrase is commented out)
            print(f"--- Verification SUCCESS for {username}: Voice matched. ---")
            return jsonify({"verified": True})

        # --- SECTION COMMENTED OUT ---
        # # --- Passphrase Verification (Only if voice matches) ---
        # print(f"--- Voice matched for {username}. Proceeding to passphrase check. ---")
        # print("--- [PRE-CHECK 2] Applying noise reduction to audio ---")
        # cleaned_audio_data = None
        # try:
        #     audio_data, sample_rate = sf.read(temp_filepath)
        #     # Ensure mono
        #     if audio_data.ndim > 1 and audio_data.shape[1] > 1:
        #         audio_data = np.mean(audio_data, axis=1)

        #     # Apply noise reduction only if audio seems reasonably loud
        #     rms = np.sqrt(np.mean(audio_data**2))
        #     if rms > 0.005: # Simple threshold to avoid amplifying noise floor
        #         cleaned_audio_data = nr.reduce_noise(y=audio_data, sr=sample_rate)
        #         print(f"Noise reduction applied for {username}.")
        #     else:
        #          print(f"Skipping noise reduction for {username}, audio RMS too low ({rms:.4f}).")
        #          cleaned_audio_data = audio_data # Use original if too quiet

        #     cleaned_filename = f"verify_{username}_cleaned_{timestamp_short}.wav"
        #     cleaned_filepath = os.path.join(TEMP_AUDIO_DIR, cleaned_filename)
        #     sf.write(cleaned_filepath, cleaned_audio_data, sample_rate)
        # except Exception as e_nr:
        #     print(f"Noise reduction failed for {username}: {e_nr}. Proceeding with original audio.")
        #     cleaned_filepath = temp_filepath # Fallback

        # print(f"--- [VERIFY CHECK 2] Running Speech Recognition for {username} ---")
        # recognizer = sr.Recognizer()
        # transcribed_text = None
        # cleaned_text = "" # Initialize cleaned_text
        # try:
        #     with sr.AudioFile(cleaned_filepath) as source:
        #         # recognizer.adjust_for_ambient_noise(source, duration=0.5)
        #         audio_for_transcription = recognizer.record(source)

        #     # Using Whisper
        #     transcribed_text = recognizer.recognize_whisper(audio_for_transcription, language="english", model="base", load_options={"download_root": os.path.join(ROOT_DIR, 'whisper_models')})
        #     if transcribed_text:
        #         cleaned_text = ''.join(c for c in transcribed_text.lower() if c.isalnum() or c.isspace()).strip()
        #         cleaned_text = ' '.join(cleaned_text.split())
        #     else:
        #          cleaned_text = ""

        #     print(f"Transcribed Text for {username}: '{cleaned_text}'")

        #     # Simple exact match check
        #     passphrase_matched = cleaned_text in ACCEPTED_PASSPHRASES

        #     if passphrase_matched:
        #         print(f"--- Verification SUCCESS for {username}: Passphrase matched. ---")
        #         return jsonify({"verified": True})
        #     else:
        #         print(f"--- Verification FAILED for {username}: Passphrase mismatch ('{cleaned_text}' not in accepted list). ---")
        #         return jsonify({"verified": False, "message": "Incorrect or unclear passphrase spoken."})

        # except sr.UnknownValueError:
        #     print(f"--- Verification FAILED for {username}: Could not understand audio for passphrase. ---")
        #     return jsonify({"verified": False, "message": "Could not understand audio. Please speak clearly."}), 400
        # except sr.RequestError as req_err:
        #     print(f"Speech recognition request error for {username}: {req_err}")
        #     # ... (Specific error checks for ffmpeg/download) ...
        #     return jsonify({"verified": False, "message": "Speech recognition service error."}), 503
        # except Exception as sr_e:
        #      print(f"Unexpected Speech Recognition error for {username}: {sr_e}")
        #      return jsonify({"verified": False, "message": "Error during speech recognition processing."}), 500
        # --- END OF SECTION COMMENTED OUT ---

    except Exception as e:
        print(f"Exception during verify flow for {username}: {e}")
        # import traceback
        # traceback.print_exc()
        return jsonify({"verified": False, "message": "An unexpected verification error occurred."}), 500
    finally:
        # Clean up temporary files
        files_to_remove = [temp_filepath] # Only remove original temp file now
        # COMMENTED OUT: Need to define cleaned_filepath or handle potential NameError if uncommenting below
        # if 'cleaned_filepath' in locals() and cleaned_filepath and cleaned_filepath != temp_filepath and os.path.exists(cleaned_filepath):
        #      files_to_remove.append(cleaned_filepath)

        for f_path in files_to_remove:
            if f_path and os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError as e:
                    print(f"Error removing temp file {f_path}: {e}")

@app.route('/api/login', methods=['POST'])
# (login endpoint remains the same)
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
             return jsonify({"login_success": False, "message": "Missing username or password."}), 400
        username, password = data['username'].lower(), data['password']
        user = read_users().get(username)
        if user and user.get('password_hash') == hash_password(password):
            user_details = {k: v for k, v in user.items() if k != 'password_hash'}
            return jsonify({"login_success": True, "user_details": user_details})
        else:
             print(f"Login failed for user: {username}")
             return jsonify({"login_success": False, "message": "Invalid username or password."}), 401
    except Exception as e:
        print(f"Error during login for {data.get('username', 'N/A')}: {e}")
        return jsonify({"login_success": False, "message": "Login failed due to server error."}), 500


@app.route('/api/visualize_gates', methods=['POST'])
# (visualize_gates endpoint remains the same)
def visualize_gates():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided."}), 400
    audio_file = request.files['audio_file']
    timestamp_short = datetime.now().strftime('%Y%m%d%H%M%S%f')
    temp_filename = f"visualize_{timestamp_short}.wav"
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, temp_filename)
    try:
        audio_file.save(temp_filepath)
        gate_data = analyze_lstm_gates(temp_filepath)
        if gate_data is None:
             print("Gate analysis returned None.")
             return jsonify({"error": "Gate analysis failed or returned no data."}), 500
        if isinstance(gate_data, dict) and "error" in gate_data:
             print(f"Gate analysis returned error: {gate_data['error']}")
             return jsonify(gate_data), 400
        return jsonify(gate_data)
    except Exception as e:
        print(f"Error during gate visualization: {e}")
        return jsonify({"error": f"Visualization failed due to server error."}), 500
    finally:
        if os.path.exists(temp_filepath):
             try: os.remove(temp_filepath)
             except OSError as e: print(f"Error removing visualization temp file {temp_filepath}: {e}")

# --- Main Execution Block ---
if __name__ == '__main__':
    print("--- Starting KeyVox Flask Development Server (Voice Only) ---")
    # Add use_reloader=False
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
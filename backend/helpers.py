import os
import tensorflow as tf
import numpy as np
import librosa

# --- Configuration ---
SAMPLE_RATE = 16000
N_MELS = 117
MAX_LEN_FRAMES = 297
N_FFT = 2048
HOP_LENGTH = 512

# =====================================================================
# --- LAZY LOADING SETUP ---
# =====================================================================

# ✅ FIX: Start with the model as None. It will be loaded on the first request.
embedding_model = None
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "lstm_model_final.h5") 

def load_model_on_demand():
    """
    This function loads the model if it hasn't been loaded yet.
    It will only run once.
    """
    global embedding_model
    if embedding_model is None:
        print("--- First request received. Loading self-contained model for the first time... ---")
        try:
            # The heavy loading operation now happens here
            embedding_model = tf.keras.models.load_model(MODEL_PATH, safe_mode=False)
            
            # "Warm up" the model to make subsequent predictions fast
            print("--- Warming up the model... ---")
            dummy_input = np.zeros((1, MAX_LEN_FRAMES, N_MELS), dtype=np.float32)
            embedding_model.predict(dummy_input, verbose=0)
            
            print("✅ Custom model is loaded, warmed up, and ready.")
        except Exception as e:
            print(f"❌ FAILED TO LOAD MODEL: {e}")
            # Re-raise to ensure the server logs the error
            raise e
            
# =====================================================================
# --- Main Embedding Function ---
# =====================================================================

def get_voice_embedding(audio_filepath):
    """
    Takes an audio file, processes it, and returns a 256-dimension voiceprint.
    """
    # ✅ FIX: Call the lazy loader at the beginning of the function
    load_model_on_demand()
    
    try:
        audio, sr = librosa.load(audio_filepath, sr=SAMPLE_RATE, mono=True)
        audio_trimmed, _ = librosa.effects.trim(audio, top_db=25)
        mel_spec = librosa.feature.melspectrogram(
            y=audio_trimmed, sr=SAMPLE_RATE, n_mels=N_MELS,
            n_fft=N_FFT, hop_length=HOP_LENGTH
        )
        log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
        features = log_mel_spec.T
        
        if features.shape[0] > MAX_LEN_FRAMES:
            features = features[:MAX_LEN_FRAMES, :]
        else:
            padding = np.zeros((MAX_LEN_FRAMES - features.shape[0], N_MELS))
            features = np.vstack((features, padding))

        features = np.expand_dims(features, axis=0)
        
        # This will now use the globally loaded model
        embedding = embedding_model.predict(features, verbose=0)
        
        return embedding[0]

    except Exception as e:
        print(f"Error processing audio file {audio_filepath}: {e}")
        return None
import os
import tensorflow as tf
import numpy as np
import librosa
import sys # Import sys for exit
import traceback # Import traceback

# --- Import necessary Keras layers ---
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import (
    Bidirectional, LSTM, Dense, Multiply, GlobalAveragePooling1D,
    GlobalMaxPooling1D, Concatenate, Dropout, Lambda, Softmax,
    BatchNormalization, Activation
)

# --- Configuration ---
SAMPLE_RATE = 16000
N_MELS = 117
MAX_LEN_FRAMES = 297
N_FFT = 2048
HOP_LENGTH = 512
INPUT_SHAPE = (MAX_LEN_FRAMES, N_MELS)

# --- Define the Model Architecture (MUST match training script EXACTLY) ---
def build_lstm_only_embedding(input_shape, embedding_dim=256):
    inp = Input(shape=input_shape, name="input_layer")
    x1 = Bidirectional(LSTM(256, return_sequences=True, dropout=0.15), name='bilstm1')(inp)
    x2 = Bidirectional(LSTM(128, return_sequences=True, dropout=0.15), name='bilstm2')(x1)
    x  = Concatenate(name='rescat')([x1, x2])  # [T, 768]
    attn_logits = Dense(1, name='attn_logits')(x)
    attn_gate   = Dense(1, activation='sigmoid', name='attn_gate')(x)
    attn_w      = Softmax(axis=1, name='attn_softmax')(attn_logits)
    xw          = Multiply(name='attn_apply')([x, attn_w])
    xw          = Multiply(name='attn_gate_apply')([xw, attn_gate])
    avg = GlobalAveragePooling1D(name='avg_pool')(xw)
    mx  = GlobalMaxPooling1D(name='max_pool')(xw)
    z   = Concatenate(name='concat_pool')([avg, mx])
    z = Dense(512, name='fc1')(z); z = BatchNormalization(name='bn1')(z); z = Activation('relu', name='relu1')(z); z = Dropout(0.30, name='drop1')(z)
    raw = Dense(256, name="raw_embeddings")(z)
    emb = Lambda(lambda t: tf.nn.l2_normalize(t, axis=-1), name="embeddings")(raw)
    return Model(inp, emb, name="lstm_only_embedding_model")

# --- Build Model and Load Weights ---
print("--- Building speaker embedding model structure ---")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ✅ CORRECT Path to the .h5 WEIGHTS file
WEIGHTS_PATH = os.path.join(BASE_DIR, "models", "full_model_v42.keras")

embedding_model = None # Initialize to None

try:
    print("Building model architecture...") # DEBUG PRINT 1
    embedding_model = build_lstm_only_embedding(INPUT_SHAPE)
    print("Model architecture built.") # DEBUG PRINT 2

    if not os.path.exists(WEIGHTS_PATH):
        print(f"❌ FATAL ERROR: Weights file not found at {WEIGHTS_PATH}")
        sys.exit(1)

    print(f"Attempting to load weights from: {WEIGHTS_PATH}") # DEBUG PRINT 3
    embedding_model.load_weights(WEIGHTS_PATH)
    print("✅ Weights loaded successfully.") # DEBUG PRINT 4

    # Perform a dummy prediction
    print("Performing dummy prediction...") # DEBUG PRINT 5
    dummy_input = np.zeros((1, MAX_LEN_FRAMES, N_MELS), dtype=np.float32)
    _ = embedding_model.predict(dummy_input, verbose=0)
    print("   Model is ready for inference.") # DEBUG PRINT 6

except ValueError as ve:
    # Catch the specific error about mismatch
    print(f"❌ FATAL ERROR: Architecture mismatch loading weights: {ve}")
    print("   Ensure 'build_lstm_only_embedding' in helpers.py EXACTLY matches the training script.")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    # Catch any other error during build or load
    print(f"❌ FATAL ERROR during model build or weight loading: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- get_voice_embedding function ---
# (Remains the same as before)
def get_voice_embedding(audio_filepath):
    """
    Takes an audio file, processes it, and returns a 256-dimension voiceprint.
    """
    if embedding_model is None:
        print("Error: Embedding model was not loaded successfully.")
        return None

    try:
        audio, sr = librosa.load(audio_filepath, sr=SAMPLE_RATE, mono=True)
        if len(audio) < HOP_LENGTH:
             print(f"Warning: Audio file {audio_filepath} is too short after loading.")
             return None
        audio_trimmed, _ = librosa.effects.trim(audio, top_db=25)
        if len(audio_trimmed) < HOP_LENGTH:
             print(f"Warning: Audio file {audio_filepath} is effectively silent or too short after trimming.")
             return None

        mel_spec = librosa.feature.melspectrogram(
            y=audio_trimmed, sr=SAMPLE_RATE, n_mels=N_MELS,
            n_fft=N_FFT, hop_length=HOP_LENGTH
        )
        log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
        features = log_mel_spec.T

        if features.shape[0] == 0:
             print(f"Warning: Could not extract features from {audio_filepath}.")
             return None

        if features.shape[0] > MAX_LEN_FRAMES:
            features = features[:MAX_LEN_FRAMES, :]
        elif features.shape[0] < MAX_LEN_FRAMES:
            padding = np.zeros((MAX_LEN_FRAMES - features.shape[0], N_MELS), dtype=np.float32)
            features = np.vstack((features, padding))

        features = np.expand_dims(features, axis=0).astype(np.float32)
        embedding = embedding_model.predict(features, verbose=0)
        return embedding[0]

    except Exception as e:
        print(f"Error processing audio file {audio_filepath}: {e}")
        return None

# (Example usage block remains the same)
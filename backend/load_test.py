import tensorflow as tf
import os
import numpy as np # Needed for dummy input

print("--- Starting Load Test ---")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "full_model_v42.keras")
print(f"Attempting to load: {MODEL_PATH}")

try:
    if not os.path.exists(MODEL_PATH):
         print("Model file not found!")
    else:
        # Define constants needed for dummy input shape
        MAX_LEN_FRAMES = 297
        N_MELS = 117

        # Load the model
        model = tf.keras.models.load_model(MODEL_PATH, safe_mode=False)
        print("✅ Model loaded successfully!")

        # Dummy predict
        print("Performing dummy prediction...")
        dummy_input = np.zeros((1, MAX_LEN_FRAMES, N_MELS), dtype=np.float32)
        _ = model.predict(dummy_input, verbose=0)
        print("   Dummy prediction successful.")

except Exception as e:
    print(f"❌ Error during load test: {e}")
    import traceback
    traceback.print_exc()

print("--- Load Test Finished ---")
# Keep it running for a moment to see the output
import time
time.sleep(5)
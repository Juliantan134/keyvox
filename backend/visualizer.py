import numpy as np
import tensorflow as tf
from helpers import embedding_model # We will create this new function

def analyze_lstm_gates(audio_filepath):
    """
    Takes an audio file, preprocesses it, and returns the average
    activations of the LSTM gates over time.
    """
    # 1. Preprocess the audio file into the correct MFCC format
    sample_to_inspect = preprocess_single_audio_file(audio_filepath)
    if sample_to_inspect is None:
        return {"error": "Could not process audio file."}

    # 2. Extract the trained weights from the first LSTM layer of the global model
    first_lstm_layer = main_model.layers[0]
    W, U, b = first_lstm_layer.get_weights()
    hidden_dim = U.shape[0]

    # Split the weight matrices into the specific weights for each of the four gates
    W_i, W_f, W_c, W_o = np.split(W, 4, axis=1)
    U_i, U_f, U_c, U_o = np.split(U, 4, axis=1)
    b_i, b_f, b_c, b_o = np.split(b, 4, axis=0)

    # 3. Manually calculate the gate activations for each time step (MFCC frame)
    h_t_minus_1 = np.zeros(hidden_dim) # Initial short-term memory (hidden state)
    c_t_minus_1 = np.zeros(hidden_dim) # Initial long-term memory (cell state)
    
    # Lists to store the average activation of all neurons in a gate at each time step
    forget_gate_activations, input_gate_activations, output_gate_activations, cell_state_values = [], [], [], []

    for t in range(sample_to_inspect.shape[0]): # Loop through each of the 200 time steps
        x_t = sample_to_inspect[t]
        
        # Forget Gate calculation (decides what old info to discard)
        f_t = tf.keras.activations.sigmoid(np.dot(x_t, W_f) + np.dot(h_t_minus_1, U_f) + b_f)
        
        # Input Gate calculation (decides what new info to store)
        i_t = tf.keras.activations.sigmoid(np.dot(x_t, W_i) + np.dot(h_t_minus_1, U_i) + b_i)
        c_tilde_t = tf.keras.activations.tanh(np.dot(x_t, W_c) + np.dot(h_t_minus_1, U_c) + b_c)
        
        # Cell State update (forgetting old info and adding new info)
        c_t = f_t * c_t_minus_1 + i_t * c_tilde_t
        
        # Output Gate calculation (decides what to output as the short-term memory)
        o_t = tf.keras.activations.sigmoid(np.dot(x_t, W_o) + np.dot(h_t_minus_1, U_o) + b_o)
        h_t = o_t * tf.keras.activations.tanh(c_t)
        
        # Store the results for this time step
        forget_gate_activations.append(np.mean(f_t.numpy()))
        input_gate_activations.append(np.mean(i_t.numpy()))
        output_gate_activations.append(np.mean(o_t.numpy()))
        cell_state_values.append(np.mean(c_t.numpy()))
        
        # Update memory for the next time step
        h_t_minus_1, c_t_minus_1 = h_t, c_t

    # 4. Return the results as a dictionary, ready to be sent as JSON
    return {
        "forget_gate": forget_gate_activations,
        "input_gate": input_gate_activations,
        "output_gate": output_gate_activations,
        "cell_state": cell_state_values,
        "time_steps": list(range(len(forget_gate_activations)))
    }
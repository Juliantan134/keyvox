import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import (Conv1D, BatchNormalization, Activation,
                                     MaxPooling1D, Bidirectional, LSTM, Dense,
                                     Multiply, GlobalAveragePooling1D, Dropout,
                                     Lambda, Softmax, GlobalMaxPooling1D, Concatenate)

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

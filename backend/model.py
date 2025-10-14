import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import (Conv1D, BatchNormalization, Activation,
                                     MaxPooling1D, Bidirectional, LSTM, Dense,
                                     Multiply, GlobalAveragePooling1D, Dropout,
                                     Lambda, Softmax, GlobalMaxPooling1D, Concatenate)

def build_embedding_model(input_shape, embedding_dim=256):
    """
    This is the CORRECT model architecture from your training script,
    using Conv1D and LSTM layers.
    """
    inp = Input(shape=input_shape, name="input_layer")

    # Convolutional blocks
    x = Conv1D(64, 5, padding='same')(inp)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling1D(2)(x)

    x = Conv1D(128, 3, padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling1D(2)(x)

    x = Conv1D(256, 3, padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling1D(2)(x)

    # Bidirectional LSTM with attention
    x = Bidirectional(LSTM(256, return_sequences=True, dropout=0.2))(x)
    attention_logits = Dense(1, name='attention_logits')(x)
    attention_weights = Softmax(axis=1, name='attention_weights')(attention_logits)
    x = Multiply()([x, attention_weights])
    x = GlobalAveragePooling1D()(x)

    # Dense layers
    x = Dense(1024)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Dropout(0.3)(x)

    x = Dense(512)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Dropout(0.2)(x)

    # Output embeddings
    raw_embeddings = Dense(embedding_dim, name="raw_embeddings")(x)
    embeddings = Lambda(lambda t: tf.nn.l2_normalize(t, axis=-1), name="embeddings")(raw_embeddings)

    return Model(inp, embeddings, name="speaker_embedding_model")
"""
Voice Emotion Recognition - Audio Preprocessing & Prediction Module
====================================================================
Teammate B imports this and calls: process_and_predict(audio_path)
It returns the predicted emotion string.

IMPORTANT: Update the CONFIG values below to match the training
pipeline EXACTLY. Ask the model trainer for these values.
"""

import os
import tempfile
import numpy as np
import librosa

# ==============================================================
# CONFIG - GET THESE FROM YOUR MODEL TRAINING TEAMMATE
# ==============================================================
CONFIG = {
    "sample_rate": 48000,        # What sample rate did they load audio at?
    "n_mfcc": 40,                # How many MFCCs?
    "n_chroma": 12,              # Chroma features? Set to 0 if not used
    "use_mel": True,             # Did they use mel spectrogram?
    "n_mels": 128,               # How many mel bands?
    "hop_length": 512,           # Hop length for feature extraction
    "n_fft": 2048,               # FFT window size
    "max_duration": 3.0,         # Fixed audio length in seconds (None if no padding/trimming)
    "trim_silence": True,        # Did they trim silence?
    "trim_threshold": 20,        # Silence threshold in dB
    "normalize_audio": True,     # Did they normalize audio amplitude?
    "average_over_time": True,   # True = flat vector, False = keep 2D sequence
}

# Output label mapping - GET THIS FROM YOUR TEAMMATE
EMOTION_LABELS = {
    0: "neutral",
    1: "calm",
    2: "happy",
    3: "sad",
    4: "angry",
    5: "fearful",
    6: "disgust",
    7: "surprised",
}

# ==============================================================
# MODEL LOADING
# ==============================================================
model = None
scaler = None


def load_model(model_path="emotion_model.h5", scaler_path=None):
    """
    Call this once when the server starts.

    Update the loading method based on what your teammate gives you:
    - Keras .h5      -> tf.keras.models.load_model(model_path)
    - PyTorch .pt    -> torch.load(model_path); model.eval()
    - Sklearn .pkl   -> joblib.load(model_path)
    - ONNX .onnx     -> ort.InferenceSession(model_path)
    """
    global model, scaler

    # EXAMPLE for Keras - uncomment and modify:
    # import tensorflow as tf
    # model = tf.keras.models.load_model(model_path)

    # EXAMPLE for PyTorch - uncomment and modify:
    # import torch
    # model = torch.load(model_path)
    # model.eval()

    # EXAMPLE for scikit-learn - uncomment and modify:
    # import joblib
    # model = joblib.load(model_path)

    # Load scaler if training used one
    if scaler_path:
        import joblib
        scaler = joblib.load(scaler_path)

    print(f"Model loaded from {model_path}")


# ==============================================================
# PREPROCESSING
# ==============================================================

def preprocess_audio(audio_path):
    """
    Takes a path to an audio file.
    Returns a feature array matching the training pipeline.
    """
    # Load audio at the correct sample rate
    y, sr = librosa.load(audio_path, sr=CONFIG["sample_rate"])

    # Trim silence
    if CONFIG["trim_silence"]:
        y, _ = librosa.effects.trim(y, top_db=CONFIG["trim_threshold"])

    # Normalize amplitude
    if CONFIG["normalize_audio"]:
        y = librosa.util.normalize(y)

    # Pad or trim to fixed length
    if CONFIG["max_duration"] is not None:
        max_samples = int(CONFIG["sample_rate"] * CONFIG["max_duration"])
        if len(y) > max_samples:
            y = y[:max_samples]
        elif len(y) < max_samples:
            y = np.pad(y, (0, max_samples - len(y)))

    # Extract features
    features = extract_features(y, sr)

    # Apply scaler if used during training
    if scaler is not None:
        features = scaler.transform(features.reshape(1, -1)).flatten()

    return features


def extract_features(y, sr):
    """
    Extract audio features matching the training pipeline.
    """
    feature_list = []

    # MFCCs
    if CONFIG["n_mfcc"] > 0:
        mfccs = librosa.feature.mfcc(
            y=y, sr=sr,
            n_mfcc=CONFIG["n_mfcc"],
            hop_length=CONFIG["hop_length"],
            n_fft=CONFIG["n_fft"],
        )
        if CONFIG["average_over_time"]:
            feature_list.append(np.mean(mfccs, axis=1))
        else:
            feature_list.append(mfccs)

    # Chroma
    if CONFIG["n_chroma"] > 0:
        chroma = librosa.feature.chroma_stft(
            y=y, sr=sr,
            hop_length=CONFIG["hop_length"],
            n_fft=CONFIG["n_fft"],
        )
        if CONFIG["average_over_time"]:
            feature_list.append(np.mean(chroma, axis=1))
        else:
            feature_list.append(chroma)

    # Mel spectrogram
    if CONFIG["use_mel"]:
        mel = librosa.feature.melspectrogram(
            y=y, sr=sr,
            n_mels=CONFIG["n_mels"],
            hop_length=CONFIG["hop_length"],
            n_fft=CONFIG["n_fft"],
        )
        if CONFIG["average_over_time"]:
            feature_list.append(np.mean(mel, axis=1))
        else:
            feature_list.append(mel)

    # Combine
    if CONFIG["average_over_time"]:
        return np.concatenate(feature_list)
    else:
        return np.concatenate(feature_list, axis=0)


# ==============================================================
# PREDICTION
# ==============================================================

def predict_emotion(features):
    """
    Run model on preprocessed features.
    Returns: predicted emotion string (e.g., "happy", "angry")
    """
    input_data = features.reshape(1, -1)

    # EXAMPLE for Keras:
    # predictions = model.predict(input_data, verbose=0)
    # predicted_index = np.argmax(predictions[0])

    # EXAMPLE for PyTorch:
    # import torch
    # with torch.no_grad():
    #     output = model(torch.FloatTensor(input_data))
    #     predicted_index = torch.argmax(output, dim=1).item()

    # EXAMPLE for scikit-learn:
    # predicted_index = model.predict(input_data)[0]

    # PLACEHOLDER - remove and uncomment your framework above
    predicted_index = 0

    return EMOTION_LABELS.get(predicted_index, "unknown")


# ==============================================================
# MAIN FUNCTION - Teammate B calls this
# ==============================================================

def process_and_predict(audio_path):
    """
    The one function Teammate B needs.

    Takes: path to audio file (saved from user upload)
    Returns: emotion string like "happy", "angry", "sad", etc.

    Usage in Teammate B's code:
        from emotion_module import load_model, process_and_predict

        load_model("emotion_model.h5")  # call once at startup

        emotion = process_and_predict("/tmp/user_audio.wav")
        # emotion = "happy"
        # now use this to build LLM prompt
    """
    features = preprocess_audio(audio_path)
    emotion = predict_emotion(features)
    return emotion

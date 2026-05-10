import torch
import torch.nn as nn
import torchaudio
import soundfile as sf
import numpy as np

EMOTION_LABELS = {0: "neutral", 1: "happy", 2: "sad", 3: "angry", 4: "fear", 5: "disgust"}

TARGET_SR = 16000
TARGET_SAMPLES = TARGET_SR * 3  # 3 seconds, matching training


class EmotionCNN(nn.Module):
    def __init__(self, num_classes=6):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(2, 2)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((16, 16))
        self.fc1 = nn.Linear(32 * 16 * 16, 128)
        self.relu3 = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool1(self.relu1(self.conv1(x)))
        x = self.pool2(self.relu2(self.conv2(x)))
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)
        x = self.relu3(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)


# Mel transform must match training exactly: sample_rate=48000 applied to 16kHz audio
_mel_transform = torch.nn.Sequential(
    torchaudio.transforms.MelSpectrogram(sample_rate=48000, n_mels=128),
    torchaudio.transforms.AmplitudeToDB(),
)

_model = None


def load_model(model_path):
    global _model
    _model = EmotionCNN(num_classes=6)
    _model.load_state_dict(torch.load(model_path, map_location="cpu"))
    _model.eval()
    print(f"EmotionCNN loaded from {model_path}")


def process_and_predict(audio_path):
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    data, sr = sf.read(audio_path, dtype="float32")
    if data.ndim == 1:
        data = data[np.newaxis, :]
    else:
        data = data.T
    waveform = torch.from_numpy(data)

    # Mono
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    # Resample to 16kHz
    if sr != TARGET_SR:
        waveform = torchaudio.transforms.Resample(orig_freq=sr, new_freq=TARGET_SR)(waveform)

    # Peak normalize
    max_val = torch.max(torch.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val

    # Trim silence
    active = torch.where(torch.abs(waveform) > 0.01)[1]
    if len(active) > 0:
        waveform = waveform[:, active[0]:active[-1] + 1]

    # Pad / truncate to 3 s
    length = waveform.shape[1]
    if length > TARGET_SAMPLES:
        waveform = waveform[:, :TARGET_SAMPLES]
    elif length < TARGET_SAMPLES:
        waveform = torch.nn.functional.pad(waveform, (0, TARGET_SAMPLES - length))

    with torch.no_grad():
        mel = _mel_transform(waveform).unsqueeze(0)  # (1, 1, 128, T)
        idx = torch.argmax(_model(mel), dim=1).item()

    return EMOTION_LABELS.get(idx, "unknown")

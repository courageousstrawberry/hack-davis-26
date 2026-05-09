import os
import torchaudio

def parse_ravdess_filename(filepath):
    # e.g., 03-01-06-01-02-01-12.wav
    filename = os.path.basename(filepath)
    parts = filename.replace('.wav', '').split('-')
    
    # Map emotion codes from the RAVDESS documentation
    emotion_map = {
        '01': 'neutral', '02': 'calm', '03': 'happy', '04': 'sad',
        '05': 'angry', '06': 'fearful', '07': 'disgust', '08': 'surprised'
    }
    
    emotion_code = parts[2]
    intensity_code = parts[3]
    actor_id = parts[6]
    
    emotion = emotion_map.get(emotion_code, 'unknown')
    intensity = 'strong' if intensity_code == '02' else 'normal'
    gender = 'female' if int(actor_id) % 2 == 0 else 'male'
    
    return emotion, intensity, gender

def create_spectrogram_torchaudio(filepath):
    # Load audio using PyTorch's audio library
    waveform, sample_rate = torchaudio.load(filepath)
    
    # Create MelSpectrogram transform (this turns audio into an image for the CNN)
    transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=sample_rate,
        n_fft=1024,
        hop_length=512,
        n_mels=64
    )
    return transform(waveform)
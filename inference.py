import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torchaudio

# Import your neural network from your train.py file
from src.train import EmotionCNN

def predict_emotion(audio_path, model_path='saved_models/combined_emotion_cnn.pth'):
    # 1. Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    emotion_map = {0: 'neutral', 1: 'happy', 2: 'sad', 3: 'angry', 4: 'fear', 5: 'disgust'}
    
    # 2. Load the "Brain"
    print("Loading model...")
    model = EmotionCNN(num_classes=6)
    
    # Load the weights safely
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval() # Freezes the brain
    
    # 3. Load and Preprocess the Single File
    print(f"Processing audio: {audio_path}")
    waveform, sample_rate = torchaudio.load(audio_path)
    
    # --- THE FIX: Convert Stereo to Mono ---
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
        print("   (Converted Stereo audio to Mono)")
        
    # Resample to 16kHz to match training data
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = resampler(waveform)
    
    # Pad or trim to exactly 3 seconds
    target_length = 3 * 16000
    if waveform.shape[1] > target_length:
        waveform = waveform[:, :target_length]
    else:
        waveform = torch.nn.functional.pad(waveform, (0, target_length - waveform.shape[1]))
    
    # Apply Mel-Spectrogram transform on the device
    mel_transform = torch.nn.Sequential(
        torchaudio.transforms.MelSpectrogram(sample_rate=16000, n_mels=128),
        torchaudio.transforms.AmplitudeToDB() 
    ).to(device)
    
    # Add batch dimension and move to GPU
    waveform = waveform.unsqueeze(0).to(device) 
    spectrogram = mel_transform(waveform)
    
    # 4. Ask the model for a prediction!
    with torch.no_grad():
        outputs = model(spectrogram)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        
        # Get the highest probability
        confidence, predicted_idx = torch.max(probabilities, 1)
        predicted_emotion = emotion_map[predicted_idx.item()]
        
    print(f"\nResult: The model is {confidence.item()*100:.1f}% confident this audio is {predicted_emotion.upper()}!")

if __name__ == '__main__':
    # Using your downloaded scream test file!
    test_file = "/home/pc/Downloads/storegraphic-crowd-cheers-314919.mp3" 
    predict_emotion(test_file)
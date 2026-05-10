import torch
import torchaudio
from src.train import EmotionCNN # (Change 'src.model' to wherever your CNN is!)

def predict_emotion(audio_path, model_path='saved_models/combined_emotion_cnn.pth'):
    # 1. Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    emotion_map = {0: 'neutral', 1: 'happy', 2: 'sad', 3: 'angry', 4: 'fear', 5: 'disgust'}
    
    # 2. Load the "Brain"
    print("Loading model...")
    model = EmotionCNN(num_classes=6)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval() # Freezes the brain so it doesn't try to learn!
    
    # 3. Load and Preprocess the Single File
    print(f"Processing audio: {audio_path}")
    waveform, sample_rate = torchaudio.load(audio_path)
    
    # Resample to 16kHz if needed (like your dataset did)
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = resampler(waveform)
    
    # Pad or trim to exactly 3 seconds
    target_length = 3 * 16000
    if waveform.shape[1] > target_length:
        waveform = waveform[:, :target_length]
    else:
        waveform = torch.nn.functional.pad(waveform, (0, target_length - waveform.shape[1]))
    
    # Apply Mel-Spectrogram transform
    mel_transform = torch.nn.Sequential(
        torchaudio.transforms.MelSpectrogram(sample_rate=16000, n_mels=128),
        torchaudio.transforms.AmplitudeToDB() 
    ).to(device)
    
    waveform = waveform.unsqueeze(0).to(device) # Add a batch dimension for the single file
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
    # You can change this path to any .wav file on your computer!
    test_file = "/home/pc/Downloads/man-scream-01.wav" 
    predict_emotion(test_file)
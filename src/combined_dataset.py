import os
import torch
import torchaudio
from torch.utils.data import Dataset

class CombinedEmotionDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        self.file_list = []
        self.target_sr = 16000
        
        # --- THE FIX: PRE-BUILD THE RESAMPLERS HERE ---
        # RAVDESS is 48kHz, TESS is 24kHz. CREMA-D is already 16kHz.
        self.resampler_48k = torchaudio.transforms.Resample(orig_freq=48000, new_freq=self.target_sr)
        self.resampler_24k = torchaudio.transforms.Resample(orig_freq=24414, new_freq=self.target_sr)
        
        self.emotion_map = {
            'neutral': 0, 'happy': 1, 'sad': 2, 'angry': 3, 'fear': 4, 'disgust': 5
        }
        
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.wav'):
                    emotion_label = self._extract_emotion(file)
                    if emotion_label is not None:
                        self.file_list.append((os.path.join(root, file), emotion_label))

    def _extract_emotion(self, filename):
        filename = filename.lower()
        
        if len(filename.split('-')) == 7:
            parts = filename.replace('.wav', '').split('-')
            if parts[1] == '01': 
                ravdess_map = {'01': 'neutral', '03': 'happy', '04': 'sad', '05': 'angry', '06': 'fear', '07': 'disgust'}
                emotion = ravdess_map.get(parts[2])
                return self.emotion_map.get(emotion) if emotion else None

        elif len(filename.split('_')) == 4 and 'xx' in filename:
            parts = filename.replace('.wav', '').split('_')
            crema_map = {'neu': 'neutral', 'hap': 'happy', 'sad': 'sad', 'ang': 'angry', 'fea': 'fear', 'dis': 'disgust'}
            emotion = crema_map.get(parts[2])
            return self.emotion_map.get(emotion) if emotion else None
            
        elif filename.startswith('oaf') or filename.startswith('yaf'):
            parts = filename.replace('.wav', '').split('_')
            emotion_word = parts[-1]
            if emotion_word == 'fear' or emotion_word == 'fearful':
                emotion = 'fear'
            else:
                emotion = emotion_word
            return self.emotion_map.get(emotion) if emotion in self.emotion_map else None
            
        return None

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        filepath, label = self.file_list[idx]
        waveform, sample_rate = torchaudio.load(filepath)
        
        # --- THE FIX: USE THE PRE-BUILT RESAMPLERS ---
        if sample_rate == 48000:
            waveform = self.resampler_48k(waveform)
            sample_rate = self.target_sr
        elif sample_rate != self.target_sr:
            # Fallback for TESS or any weirdly formatted files
            waveform = self.resampler_24k(waveform)
            sample_rate = self.target_sr
            
        # Peak Normalization
        max_val = torch.max(torch.abs(waveform))
        if max_val > 0:
            waveform = waveform / max_val
            
        # Silence Trimming
        threshold = 0.01
        abs_wave = torch.abs(waveform)
        active_indices = torch.where(abs_wave > threshold)[1]
        
        if len(active_indices) > 0:
            start_idx = active_indices[0]
            end_idx = active_indices[-1]
            waveform = waveform[:, start_idx:end_idx+1]
            
        # Fixed Length Padding/Truncating (Target: 3 seconds)
        target_length = 3 * sample_rate 
        current_length = waveform.shape[1]
        
        if current_length > target_length:
            waveform = waveform[:, :target_length]
        elif current_length < target_length:
            pad_amount = target_length - current_length
            waveform = torch.nn.functional.pad(waveform, (0, pad_amount))
            
        if self.transform:
            waveform = self.transform(waveform)
            
        return waveform, label
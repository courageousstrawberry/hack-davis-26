import os
import torch
import torchaudio
from torch.utils.data import Dataset

class CombinedEmotionDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        self.file_list = []
        
        # Universal mapping for the 6 common emotions shared by RAVDESS, TESS, and CREMA-D
        self.emotion_map = {
            'neutral': 0,
            'happy': 1,
            'sad': 2,
            'angry': 3,
            'fear': 4,
            'disgust': 5
        }
        
        # Parse all files in the directory recursively
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.wav'):
                    emotion_label = self._extract_emotion(file)
                    # Only add the file if it matches one of our 6 common emotions
                    if emotion_label is not None:
                        self.file_list.append((os.path.join(root, file), emotion_label))

    def _extract_emotion(self, filename):
        """
        Detects which dataset the file comes from based on naming conventions,
        and returns the standardized emotion integer.
        """
        filename = filename.lower()
        
        # 1. RAVDESS Format: 03-01-05-01-02-01-12.wav
        if len(filename.split('-')) == 7:
            parts = filename.replace('.wav', '').split('-')
            if parts[1] == '01': # Check if it's speech (01), skip song (02)
                ravdess_map = {
                    '01': 'neutral',
                    # '02' is calm (dropped)
                    '03': 'happy',
                    '04': 'sad',
                    '05': 'angry',
                    '06': 'fear',
                    '07': 'disgust'
                    # '08' is surprised (dropped)
                }
                emotion = ravdess_map.get(parts[2])
                return self.emotion_map.get(emotion) if emotion else None

        # 2. CREMA-D Format: 1001_DFA_ANG_XX.wav
        elif len(filename.split('_')) == 4 and 'xx' in filename:
            parts = filename.replace('.wav', '').split('_')
            crema_map = {
                'neu': 'neutral',
                'hap': 'happy',
                'sad': 'sad',
                'ang': 'angry',
                'fea': 'fear',
                'dis': 'disgust'
            }
            emotion = crema_map.get(parts[2])
            return self.emotion_map.get(emotion) if emotion else None
            
        # 3. TESS Format: OAF_back_angry.wav or YAF_dog_happy.wav
        elif filename.startswith('oaf') or filename.startswith('yaf'):
            parts = filename.replace('.wav', '').split('_')
            emotion_word = parts[-1]
            
            # TESS uses 'fearful' sometimes instead of 'fear'
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
        
        # Load the audio
        waveform, sample_rate = torchaudio.load(filepath)
        
        # --- PRE-PROCESSING TECHNIQUES ---
        
        # STEP 1: UNIFORM RESAMPLING
        # Force all datasets (RAVDESS 48k, TESS 24k, CREMA 16k) to 16,000 Hz
        target_sr = 16000
        if sample_rate != target_sr:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)
            waveform = resampler(waveform)
            sample_rate = target_sr
            
        # STEP 2: PEAK NORMALIZATION
        max_val = torch.max(torch.abs(waveform))
        if max_val > 0:
            waveform = waveform / max_val
            
        # STEP 3: SILENCE TRIMMING
        threshold = 0.01
        abs_wave = torch.abs(waveform)
        active_indices = torch.where(abs_wave > threshold)[1]
        
        if len(active_indices) > 0:
            start_idx = active_indices[0]
            end_idx = active_indices[-1]
            waveform = waveform[:, start_idx:end_idx+1]
            
        # STEP 4: FIXED LENGTH PADDING/TRUNCATING (Target: 3 seconds)
        target_length = 3 * sample_rate # 3 * 16000 = 48000
        current_length = waveform.shape[1]
        
        if current_length > target_length:
            # Truncate
            waveform = waveform[:, :target_length]
        elif current_length < target_length:
            # Pad
            pad_amount = target_length - current_length
            waveform = torch.nn.functional.pad(waveform, (0, pad_amount))
            
        # --- END PRE-PROCESSING ---
        
        # Apply Transform (MelSpectrogram)
        if self.transform:
            waveform = self.transform(waveform)
            
        return waveform, label
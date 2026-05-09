        # --- PRE-PROCESSING TECHNIQUES ---
        
        # TECHNIQUE 1: Peak Normalization
        # Normalize first so the loudest point is 1.0. This makes setting a silence threshold easier.
        max_val = torch.max(torch.abs(waveform))
        if max_val > 0:
            waveform = waveform / max_val
            
        # TECHNIQUE 2: Silence Trimming
        # Remove audio where the volume is less than 1% of the peak (0.01 threshold)
        threshold = 0.01
        abs_wave = torch.abs(waveform)
        # Find all indices where the volume exceeds the threshold
        active_indices = torch.where(abs_wave > threshold)[1]
        
        if len(active_indices) > 0:
            # Find the first and last time the threshold was exceeded
            start_idx = active_indices[0]
            end_idx = active_indices[-1]
            # Slice the tensor to keep only the active speech portion
            waveform = waveform[:, start_idx:end_idx+1]
            
        # TECHNIQUE 3: Fixed Length Padding/Truncating (Target: 3 seconds)
        target_length = 3 * sample_rate # 3 seconds
        current_length = waveform.shape[1]
        
        if current_length > target_length:
            # Truncate if too long
            waveform = waveform[:, :target_length]
        elif current_length < target_length:
            # Pad with zeros if too short
            pad_amount = target_length - current_length
            waveform = torch.nn.functional.pad(waveform, (0, pad_amount))
            
        # --- END PRE-PROCESSING ---
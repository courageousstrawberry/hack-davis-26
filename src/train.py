import torch
import torch.nn as nn
import torch.optim as optim
import torchaudio
from torch.utils.data import DataLoader, random_split
import os

# Import the classes we just made
from dataset import RAVDESSDataset
from model import EmotionCNN

def train_model():
    # 1. SETUP HARDWARE
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    # 2. PREPARE DATA
    # Define the transform to turn audio into a Mel-spectrogram
    mel_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=48000, 
        n_mels=64
    )
    
    # Load dataset
    print("Loading dataset...")
    # Using relative path '../data/raw' assuming you run this from inside the src/ folder
    dataset = RAVDESSDataset(data_dir='../data/raw', transform=mel_transform)
    
    # 2.5 SPLIT DATA INTO TRAIN AND VALIDATION SETS
    # Standard 80% train / 20% validation split
    total_size = len(dataset)
    train_size = int(0.8 * total_size)
    val_size = total_size - train_size
    
    # random_split ensures the model is tested on audio it didn't memorize during training
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    # Create DataLoaders for both sets
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    # 3. INITIALIZE THE MODEL
    model = EmotionCNN(num_classes=8).to(device)
    
    # 4. DEFINE LOSS AND OPTIMIZER
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 5. TRAINING LOOP
    num_epochs = 20
    print("Starting training...")
    
    for epoch in range(num_epochs):
        # --- TRAINING PHASE ---
        model.train() # Set model to training mode
        running_train_loss = 0.0
        
        for waveforms, labels in train_loader:
            waveforms, labels = waveforms.to(device), labels.to(device)
            
            optimizer.zero_grad()
            predictions = model(waveforms)
            loss = criterion(predictions, labels)
            
            loss.backward()
            optimizer.step()
            running_train_loss += loss.item()
            
        avg_train_loss = running_train_loss / len(train_loader)
        
        # --- VALIDATION PHASE ---
        model.eval() # Set model to evaluation mode (turns off dropout/batchnorm updates)
        running_val_loss = 0.0
        correct_predictions = 0
        total_predictions = 0
        
        # Use torch.no_grad() to save memory and speed up validation
        with torch.no_grad():
            for waveforms, labels in val_loader:
                waveforms, labels = waveforms.to(device), labels.to(device)
                
                predictions = model(waveforms)
                loss = criterion(predictions, labels)
                running_val_loss += loss.item()
                
                # Calculate accuracy
                _, predicted_classes = torch.max(predictions, 1)
                total_predictions += labels.size(0)
                correct_predictions += (predicted_classes == labels).sum().item()
                
        avg_val_loss = running_val_loss / len(val_loader)
        val_accuracy = 100 * correct_predictions / total_predictions
        
        print(f"Epoch [{epoch+1}/{num_epochs}] "
              f"| Train Loss: {avg_train_loss:.4f} "
              f"| Val Loss: {avg_val_loss:.4f} "
              f"| Val Accuracy: {val_accuracy:.2f}%")

    # 6. SAVE THE TRAINED MODEL
    os.makedirs('../checkpoints', exist_ok=True)
    save_path = '../checkpoints/emotion_model_v1.pth'
    torch.save(model.state_dict(), save_path)
    print(f"Training complete! Model saved to {save_path}")

if __name__ == "__main__":
    train_model()
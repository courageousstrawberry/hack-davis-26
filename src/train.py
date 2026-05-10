import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchaudio
from torch.utils.data import DataLoader, random_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# Import the new combined dataset
from src.combined_dataset import CombinedEmotionDataset

# ---------------------------------------------------------
# 1. DEFINE THE NEURAL NETWORK (Your Original Model)
# ---------------------------------------------------------
class EmotionCNN(nn.Module):
    def __init__(self, num_classes=6): 
        super(EmotionCNN, self).__init__()
        
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
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
        x = self.fc2(x)
        return x

# ---------------------------------------------------------
# 2. MAIN TRAINING SCRIPT
# ---------------------------------------------------------
def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    batch_size = 256
    learning_rate = 0.001
    num_epochs = 30
    data_dir = './data/train' 

    mel_transform = torch.nn.Sequential(
        torchaudio.transforms.MelSpectrogram(sample_rate=48000, n_mels=128),
        torchaudio.transforms.AmplitudeToDB() 
    ).to(device)

    print("Loading dataset...")
    full_dataset = CombinedEmotionDataset(data_dir=data_dir)
    
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(
        dataset=train_dataset, batch_size=batch_size, 
        shuffle=True, num_workers=8, pin_memory=True
    )
    
    val_loader = DataLoader(
        dataset=val_dataset, batch_size=batch_size, 
        shuffle=False, num_workers=8, pin_memory=True
    )

    model = EmotionCNN(num_classes=6).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    os.makedirs('saved_models', exist_ok=True)
    best_val_loss = float('inf')
    patience = 5
    epochs_without_improvement = 0

    print(f"Starting training for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        model.train() 
        running_loss = 0.0

        for batch_idx, (batch_audio, batch_labels) in enumerate(train_loader):
            batch_audio = batch_audio.to(device)
            batch_labels = batch_labels.to(device)

            batch_audio = mel_transform(batch_audio)
            # --- NEW: LIVE BATCH PROGRESS TRACKER ---
            # end='\r' overwrites the line so it looks like an updating animation!
            print(f"Epoch [{epoch+1}/{num_epochs}] | Processing batch {batch_idx+1}/{len(train_loader)}...", end='\r')

            optimizer.zero_grad()
            outputs = model(batch_audio)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        # Clears the batch progress line before printing the validation stats
        print(" " * 80, end="\r")
        epoch_train_loss = running_loss / len(train_loader)

        # --- VALIDATION PHASE ---
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch_audio, batch_labels in val_loader:
                batch_audio = batch_audio.to(device)
                batch_labels = batch_labels.to(device)

                batch_audio = mel_transform(batch_audio)

                outputs = model(batch_audio)
                loss = criterion(outputs, batch_labels)
                val_loss += loss.item()

                _, predicted = torch.max(outputs.data, 1)
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(batch_labels.cpu().numpy())

        epoch_val_loss = val_loss / len(val_loader)

        acc = accuracy_score(all_labels, all_preds)
        prec = precision_score(all_labels, all_preds, average='macro', zero_division=0)
        rec = recall_score(all_labels, all_preds, average='macro', zero_division=0)
        f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)

        print(f"Epoch [{epoch+1}/{num_epochs}] | "
              f"Train Loss: {epoch_train_loss:.4f} | "
              f"Val Loss: {epoch_val_loss:.4f} | "
              f"Acc: {acc*100:.2f}% | "
              f"F1: {f1:.4f} | "
              f"Prec: {prec:.4f} | "
              f"Rec: {rec:.4f}")

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            epochs_without_improvement = 0
            torch.save(model.state_dict(), 'saved_models/combined_emotion_cnn.pth')
            print("   --> Validation loss decreased! Best model saved.")
        else:
            epochs_without_improvement += 1
            print(f"   --> No improvement for {epochs_without_improvement} epochs.")
            
        if epochs_without_improvement >= patience:
            print("Early stopping triggered! Training stopped to prevent overfitting.")
            break

    print("Training complete! Your best model is saved at 'saved_models/combined_emotion_cnn.pth'")

if __name__ == '__main__':
    main()


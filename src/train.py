import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchaudio
from torch.utils.data import DataLoader

# Import the new combined dataset
from src.combined_dataset import CombinedEmotionDataset

# ---------------------------------------------------------
# 1. DEFINE THE NEURAL NETWORK
# ---------------------------------------------------------
class EmotionCNN(nn.Module):
    def __init__(self, num_classes=6): # Changed default to 6 classes
        super(EmotionCNN, self).__init__()
        
        # First Convolutional Block
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, padding=1)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Second Convolutional Block
        self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Adaptive pooling ensures the output is always 16x16
        self.adaptive_pool = nn.AdaptiveAvgPool2d((16, 16))
        
        # Fully Connected Layers
        self.fc1 = nn.Linear(32 * 16 * 16, 128)
        self.relu3 = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        
        # Final output layer
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

    batch_size = 32
    learning_rate = 0.001
    num_epochs = 30
    
    # Point this to your combined training data directory
    data_dir = './data/train' 

    mel_transform = torch.nn.Sequential(
        torchaudio.transforms.MelSpectrogram(sample_rate=48000, n_mels=128),
        torchaudio.transforms.AmplitudeToDB() 
    )

    print("Loading dataset...")
    # Use the new CombinedEmotionDataset
    train_dataset = CombinedEmotionDataset(data_dir=data_dir, transform=mel_transform)
    
    train_loader = DataLoader(
        dataset=train_dataset,
        batch_size=32,
        shuffle=True,
        num_workers=8,
        pin_memory=True
    )

    # Initialize model with 6 classes
    model = EmotionCNN(num_classes=6).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    print(f"Starting training for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        model.train() 
        running_loss = 0.0
        correct_predictions = 0
        total_samples = 0

        for batch_idx, (batch_audio, batch_labels) in enumerate(train_loader):
            batch_audio = batch_audio.to(device)
            batch_labels = batch_labels.to(device)
            print(f"Loading batch {batch_idx} / {len(train_loader)}")
            batch_audio = batch_audio.to(device)
            batch_labels = batch_labels.to(device)

            optimizer.zero_grad()
            outputs = model(batch_audio)
            
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total_samples += batch_labels.size(0)
            correct_predictions += (predicted == batch_labels).sum().item()

        epoch_loss = running_loss / len(train_loader)
        epoch_acc = 100 * correct_predictions / total_samples
        print(f"Epoch [{epoch+1}/{num_epochs}] | Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.2f}%")

    print("Training complete!")
    os.makedirs('saved_models', exist_ok=True)
    torch.save(model.state_dict(), 'saved_models/combined_emotion_cnn.pth')
    print("Model weights saved to 'saved_models/combined_emotion_cnn.pth'")

if __name__ == '__main__':
    main()
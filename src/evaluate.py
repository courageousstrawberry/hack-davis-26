import torch
import torchaudio
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report

# Import your custom dataset and the CNN architecture
from dataset import RAVDESSDataset
from train import EmotionCNN

def main():
    # 1. Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 2. Define the exact same transform used during training
    mel_transform = torch.nn.Sequential(
        torchaudio.transforms.MelSpectrogram(sample_rate=48000, n_mels=128),
        torchaudio.transforms.AmplitudeToDB()
    )

    # 3. Load the Test Dataset
    # Make sure this directory contains data the model HAS NOT seen during training
    test_data_dir = './data/test' 
    test_dataset = RAVDESSDataset(data_dir=test_data_dir, transform=mel_transform)
    test_loader = DataLoader(dataset=test_dataset, batch_size=32, shuffle=False)

    # 4. Initialize the model and load the saved weights
    model = EmotionCNN(num_classes=8).to(device)
    model.load_state_dict(torch.load('saved_models/emotion_cnn.pth'))
    
    # Put the model in evaluation mode (disables Dropout and BatchNorm)
    model.eval()

    # Variables to track performance
    all_predictions = []
    all_true_labels = []
    correct = 0
    total = 0

    print("Evaluating model...")
    
    # 5. Disable gradient calculation for inference
    with torch.no_grad():
        for batch_audio, batch_labels in test_loader:
            batch_audio = batch_audio.to(device)
            batch_labels = batch_labels.to(device)

            # Get model predictions
            outputs = model(batch_audio)
            
            # The highest output value is the predicted class
            _, predicted = torch.max(outputs.data, 1)

            # Keep track of correct predictions
            total += batch_labels.size(0)
            correct += (predicted == batch_labels).sum().item()

            # Store predictions for the classification report
            all_predictions.extend(predicted.cpu().numpy())
            all_true_labels.extend(batch_labels.cpu().numpy())

    # 6. Print Results
    accuracy = 100 * correct / total
    print(f"\nOverall Test Accuracy: {accuracy:.2f}%")

    # Map the integer labels back to the emotion strings for the report
    target_names = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
    
    print("\nDetailed Classification Report:")
    print(classification_report(all_true_labels, all_predictions, target_names=target_names))

if __name__ == '__main__':
    main()
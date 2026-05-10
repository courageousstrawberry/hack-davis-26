import torch
import torchaudio
import seaborn as sns
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix

# Import your custom dataset and the CNN architecture
from dataset import CombinedEmotionDataset
from train import EmotionCNN

def main():
    # 1. Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 2. Define the EXACT same transform used during training (Note the 16000 Hz sample rate!)
    mel_transform = torch.nn.Sequential(
        torchaudio.transforms.MelSpectrogram(sample_rate=16000, n_mels=128),
        torchaudio.transforms.AmplitudeToDB()
    )

    # 3. Load the Test Dataset
    # Point this to your test directory containing the 20% unseen split
    test_data_dir = './data/test' 
    print("Loading test dataset...")
    test_dataset = CombinedEmotionDataset(data_dir=test_data_dir, transform=mel_transform)
    test_loader = DataLoader(dataset=test_dataset, batch_size=32, shuffle=False)

    # 4. Initialize the model and load the saved weights
    # Ensure num_classes is 6 for the combined dataset
    model = EmotionCNN(num_classes=6).to(device)
    model.load_state_dict(torch.load('saved_models/combined_emotion_cnn.pth'))
    
    # Put the model in evaluation mode (turns off dropout)
    model.eval()

    # Variables to track performance
    all_predictions = []
    all_true_labels = []
    correct = 0
    total = 0

    print("Evaluating model. This may take a moment depending on the dataset size...")
    
    # 5. Disable gradient calculation for fast inference
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

            # Store predictions for the metrics and matrix
            all_predictions.extend(predicted.cpu().numpy())
            all_true_labels.extend(batch_labels.cpu().numpy())

    # 6. Calculate Overall Accuracy
    accuracy = 100 * correct / total
    print(f"\nOverall Test Accuracy: {accuracy:.2f}%")

    # 7. Print the Classification Report (Precision, Recall, F1-Score)
    # Target names match the 0-5 mapping in dataset.py
    target_names = ['Neutral', 'Happy', 'Sad', 'Angry', 'Fear', 'Disgust']
    
    print("\nDetailed Classification Report:")
    print(classification_report(all_true_labels, all_predictions, target_names=target_names))

    # 8. Generate and Save the Confusion Matrix Heatmap
    print("\nGenerating Confusion Matrix...")
    cm = confusion_matrix(all_true_labels, all_predictions)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=target_names, yticklabels=target_names)
    
    plt.title('Emotion Confusion Matrix (Test Set)')
    plt.ylabel('True Emotion')
    plt.xlabel('Predicted Emotion')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    print("Saved confusion matrix heatmap to 'confusion_matrix.png'")

if __name__ == '__main__':
    main()
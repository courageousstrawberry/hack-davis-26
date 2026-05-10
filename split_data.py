import os
import shutil

def split_ravdess_dataset(source_dir, train_dir, test_dir):
    """
    Splits the RAVDESS dataset into train and test sets based on Actor ID.
    Actors 1-19 (approx 80%) go to train, Actors 20-24 (approx 20%) go to test.
    """
    # Create the target directories if they don't exist
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)
    
    # Define which actors go to the test set
    test_actors = ['20', '21', '22', '23', '24']
    
    files_moved_train = 0
    files_moved_test = 0
    
    # Walk through all subfolders (Actor_01, Actor_02, etc.)
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.wav'):
                # Grab the Actor ID from the filename
                filename_no_ext = file.replace('.wav', '')
                parts = filename_no_ext.split('-')
                
                if len(parts) == 7:
                    actor_id = parts[6]
                    src_path = os.path.join(root, file)
                    
                    # Route to Train or Test based on Actor ID
                    if actor_id in test_actors:
                        dest_path = os.path.join(test_dir, file)
                        files_moved_test += 1
                    else:
                        dest_path = os.path.join(train_dir, file)
                        files_moved_train += 1
                        
                    # Copy the file (safer than moving)
                    shutil.copy2(src_path, dest_path)

    print(f"Dataset split complete!")
    print(f"Copied {files_moved_train} files to {train_dir}")
    print(f"Copied {files_moved_test} files to {test_dir}")

if __name__ == '__main__':
    # UPDATE THIS to wherever your raw RAVDESS folders are currently sitting
    SOURCE_DIRECTORY = './raw_ravdess_data' 
    
    # These are the directories train.py and evaluate.py will use
    TRAIN_DIRECTORY = './data/train'
    TEST_DIRECTORY = './data/test'
    
    split_ravdess_dataset(SOURCE_DIRECTORY, TRAIN_DIRECTORY, TEST_DIRECTORY)
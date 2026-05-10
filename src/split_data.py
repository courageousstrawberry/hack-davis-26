import os
import shutil
import random

def split_combined_datasets(source_dir, train_dir, test_dir):
    """
    Splits RAVDESS, CREMA-D, and TESS into 80% train and 20% test sets.
    Performs speaker-independent splits for RAVDESS and CREMA-D.
    """
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)
    
    # 1. RAVDESS: Test Actors 20-24
    ravdess_test_actors = ['20', '21', '22', '23', '24']
    
    # 2. CREMA-D: Test Actors 1074-1091 (approx 20% of the 91 actors)
    crema_test_actors = [str(i) for i in range(1074, 1092)]
    
    # 3. TESS: 20% random split 
    tess_files = []
    
    files_moved_train = 0
    files_moved_test = 0

    print("Scanning and splitting files...")
    
    for root, _, files in os.walk(source_dir):
        for file in files:
            if not file.endswith('.wav'):
                continue
                
            filename = file.lower()
            src_path = os.path.join(root, file)
            dest_path = None
            
            # --- RAVDESS ---
            if len(filename.split('-')) == 7:
                actor_id = filename.replace('.wav', '').split('-')[6]
                if actor_id in ravdess_test_actors:
                    dest_path = os.path.join(test_dir, file)
                    files_moved_test += 1
                else:
                    dest_path = os.path.join(train_dir, file)
                    files_moved_train += 1
                    
            # --- CREMA-D ---
            elif len(filename.split('_')) == 4 and 'xx' in filename:
                actor_id = filename.split('_')[0]
                if actor_id in crema_test_actors:
                    dest_path = os.path.join(test_dir, file)
                    files_moved_test += 1
                else:
                    dest_path = os.path.join(train_dir, file)
                    files_moved_train += 1
                    
            # --- TESS ---
            elif filename.startswith('oaf') or filename.startswith('yaf'):
                # Store TESS files for random splitting later
                tess_files.append((src_path, file))
                continue # Skip the copy step for now
                
            # Copy RAVDESS and CREMA-D files
            if dest_path:
                shutil.copy2(src_path, dest_path)
                
    # Process TESS random split
    if tess_files:
        print(f"Splitting {len(tess_files)} TESS files...")
        random.shuffle(tess_files)
        split_idx = int(len(tess_files) * 0.8)
        
        # Train TESS
        for src, fname in tess_files[:split_idx]:
            shutil.copy2(src, os.path.join(train_dir, fname))
            files_moved_train += 1
            
        # Test TESS
        for src, fname in tess_files[split_idx:]:
            shutil.copy2(src, os.path.join(test_dir, fname))
            files_moved_test += 1

    print(f"\nDataset split complete!")
    print(f"Total files in Train Set: {files_moved_train}")
    print(f"Total files in Test Set: {files_moved_test}")

if __name__ == '__main__':
    # Make sure to put all your unzipped RAVDESS, CREMA-D, and TESS folders inside this 'raw_data' folder
    SOURCE_DIRECTORY = './raw_data' 
    TRAIN_DIRECTORY = './data/train'
    TEST_DIRECTORY = './data/test'
    
    # Set a random seed so TESS splits the exact same way if you run it twice
    random.seed(42)
    split_combined_datasets(SOURCE_DIRECTORY, TRAIN_DIRECTORY, TEST_DIRECTORY)
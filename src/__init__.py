    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        
        # FILTER OUT SINGING
        self.file_list = []
        for f in os.listdir(data_dir):
            if f.endswith('.wav'):
                parts = f.replace('.wav', '').split('-')
                
                # Verify filename structure and check if Vocal Channel is '01' (Speech)
                if len(parts) == 7 and parts[1] == '01':
                    self.file_list.append(f)
        
        # Map emotion codes to integer labels
        self.emotion_map = {
            '01': 0, '02': 1, '03': 2, '04': 3,
            '05': 4, '06': 5, '07': 6, '08': 7
        }
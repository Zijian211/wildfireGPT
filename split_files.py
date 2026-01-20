import os

# Define chunk size (50MB is safe for GitHub)
CHUNK_SIZE = 50 * 1024 * 1024 

files_to_split = [
    "data/wildfire_index.bin.gz",
    "data/document_embeddings.pkl.gz"
]

print("✂️  Starting file split operation...")

for file_path in files_to_split:
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        continue
        
    file_name = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)
    
    # Read the big file and write chunks
    with open(file_path, 'rb') as f:
        part_num = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            
            # Create part filename: e.g., wildfire_index.bin.gz.part000
            part_name = f"{file_path}.part{part_num:03d}"
            
            with open(part_name, 'wb') as p:
                p.write(chunk)
                
            print(f"   Created chunk: {part_name}")
            part_num += 1

print("✅ Splitting complete! You can now upload the .part files.")
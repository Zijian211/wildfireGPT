import gzip
import shutil
import os

files_to_compress = [
    "data/wildfire_index.bin",
    "data/document_embeddings.pkl"
]

print("⏳ Starting compression job...")

for file_path in files_to_compress:
    if os.path.exists(file_path):
        output_path = file_path + ".gz"
        print(f"📦 Compressing {file_path} -> {output_path}...")
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        print(f"⚠️ Could not find {file_path}, skipping...")

print("✅ Compression complete! You can now upload the .gz files.")
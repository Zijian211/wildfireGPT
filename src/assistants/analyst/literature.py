import pandas as pd
import requests
import gzip
import shutil
import tempfile
import os
import glob
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np

# --- HELPER: Reassemble split files ---
def get_assembled_file_path(original_filename):
    """
    Checks if the file exists. If not, tries to reassemble it from .partXXX chunks.
    Returns the path to the usable file.
    """
    base_path = f"./data/{original_filename}"
    
    # If the file is already there (local machine), just use it
    if os.path.exists(base_path):
        return base_path

    # If not, look for parts (e.g., file.gz.part000)
    # We stitch them into a temp file
    part_pattern = f"{base_path}.part*"
    parts = sorted(glob.glob(part_pattern))
    
    if not parts:
        raise FileNotFoundError(f"Could not find {original_filename} or its parts in ./data/")

    # Create a temp file to hold the stitched data
    # We use delete=False so we can read it later
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gz") as tmp_assembled:
        for part in parts:
            with open(part, "rb") as p:
                shutil.copyfileobj(p, tmp_assembled)
        assembled_path = tmp_assembled.name
    
    return assembled_path

# --- CORE FUNCTIONS ---

def get_doi_by_title(title):
    url = "https://api.crossref.org/works"
    params = {"query.title": title}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            items = response.json().get("message", {}).get("items", [])
            return items[0].get("DOI") if items else "No results found"
    except:
        pass
    return "Failed to fetch data"

# 1. Load CSV (Uses the helper logic automatically if needed)
# Note: For the CSV, we assume it's small enough or handled similarly. 
# If you split the CSV too, use the helper. If not, leave as is.
csv_path = "./data/wildfire_literature.csv.gz"
if not os.path.exists(csv_path):
    # Fallback if you decided to split the CSV too (optional)
    pass 
df = pd.read_csv(csv_path)
df['combined_text'] = df['title'] + ' ' + df['abstract'] + ' ' + df['field']


# 2. Load FAISS Index (Stitch -> Unzip -> Load)
index_gz_path = get_assembled_file_path("wildfire_index.bin.gz")

# Unzip the (potentially stitched) GZ to a raw binary temp file for FAISS
with tempfile.NamedTemporaryFile(delete=False) as tmp_index:
    with gzip.open(index_gz_path, 'rb') as f_in:
        shutil.copyfileobj(f_in, tmp_index)
    temp_index_name = tmp_index.name

index = faiss.read_index(temp_index_name)
os.remove(temp_index_name) # Cleanup raw binary


# 3. Load Embeddings (Stitch -> Load)
# We don't use this variable in the search function below, but loading it to match your original code
emb_gz_path = get_assembled_file_path("document_embeddings.pkl.gz")
with gzip.open(emb_gz_path, "rb") as f:
    embeddings = pickle.load(f)


# Load Model
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

def search(query, k=3):
    query_vector = model.encode([query]).astype(np.float32)
    _, indices = index.search(query_vector, k)
    return df.iloc[indices[0]].reset_index(drop=True)
    
def get_author(authors_str):
    import ast
    try:
        authors = ast.literal_eval(authors_str)
        if len(authors) > 3:
            formatted = f"{authors[0]['first']} {authors[0]['last']} et al."
        else:
            formatted = ', '.join(f"{author['first']} {author['last']}" for author in authors)
        return formatted
    except:
        return authors_str

def literature_search(query):
    results = search(query).to_dict('records')
    message = f"Here are the 3 most relevant papers for your query '{query}':\n\n"
    
    for i, result in enumerate(results):
        # Basic DOI fetch (can be slow, consider caching or skipping in dev)
        result['doi'] = get_doi_by_title(result['title'])
        
        message += f"{i+1}. Title: {result['title']}\n"
        message += f"Authors: {get_author(result['authors'])}\n"
        message += f"Year: {result['year']}\n"
        if "doi.org" not in str(result['doi']) and result['doi'] not in ["No results found", "Failed to fetch data"]:
             message += f"DOI: https://doi.org/{result['doi']}\n"
        else:
             message += f"DOI: {result['doi']}\n"
        message += f"Abstract: {result['abstract']}\n\n"
        
    return message

if __name__ == "__main__":
    query = "wildfire mitigation strategies"
    print(literature_search(query))
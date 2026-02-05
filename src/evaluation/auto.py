from sentence_transformers import SentenceTransformer
import torch

# --- Load Model Once ---
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
cossim = torch.nn.CosineSimilarity(dim=0, eps=1e-6)

def score_sbert_similarity(text1, text2):
    """
    Calculates the cosine similarity between two texts.
    SAFEGUARD: Handles cases where input is a Tuple (text, visuals) or None.
    """
    # --- 1. Safety Check: Handle None ---
    if text1 is None: text1 = ""
    if text2 is None: text2 = ""

    # --- 2. Safety Check: Extract Text from Tuples ---
    # The system often returns (response_text, [list_of_images])
    if isinstance(text1, tuple): 
        text1 = str(text1[0])
    if isinstance(text2, tuple): 
        text2 = str(text2[0])

    # --- 3. Ensure String Format ---
    text1 = str(text1)
    text2 = str(text2)

    # --- 4. Encode and Score ---
    embeddings = sbert_model.encode([text1, text2], convert_to_tensor=True)
    return cossim(embeddings[0], embeddings[1]).item()
import numpy as np
import faiss

from src.gemini_client import embed_texts, embed_query

def build_faiss_index(client, chunks):
    # Batch to avoid overly large embedding requests.
    vectors = []
    batch = 80
    for i in range(0, len(chunks), batch):
        vectors.extend(embed_texts(client, chunks[i:i+batch]))
    arr = np.asarray(vectors, dtype="float32")
    if arr.ndim != 2 or len(arr) != len(chunks):
        raise ValueError("Embedding generation returned an unexpected shape.")
    faiss.normalize_L2(arr)
    index = faiss.IndexFlatIP(arr.shape[1])
    index.add(arr)
    return index

def retrieve(client, index, chunks, metadata, query, k=8):
    if index is None or not chunks:
        return []
    q = np.asarray([embed_query(client, query)], dtype="float32")
    faiss.normalize_L2(q)
    k = min(k, len(chunks))
    scores, ids = index.search(q, k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0:
            continue
        results.append({
            "score": float(score),
            "text": chunks[idx],
            "metadata": metadata[idx] if idx < len(metadata) else {},
        })
    return results

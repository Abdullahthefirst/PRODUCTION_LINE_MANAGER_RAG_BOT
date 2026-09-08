from google import genai
from google.genai import types

GENERATION_MODEL = "gemini-3.6-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

AUTH_MARKERS = (
    "api_key_invalid",
    "api key not valid",
    "invalid api key",
    "invalid_argument",
    "permission_denied",
    "unauthenticated",
    "authentication",
    "401",
    "403",
)

def create_client(api_key: str):
    return genai.Client(api_key=api_key)

def is_auth_error(exc: Exception) -> bool:
    text = str(exc).lower()
    # Do not treat quota/rate limit as a bad key.
    if any(x in text for x in ("quota", "rate limit", "resource_exhausted", "429")):
        return False
    return any(marker in text for marker in AUTH_MARKERS)

def validate_key(api_key: str):
    client = create_client(api_key)

    # Validate credentials/model access without doing generation.
    model = client.models.get(model=GENERATION_MODEL)

    return client, model is not None
def generate_text(client, prompt: str, max_output_tokens: int = 1800) -> str:
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_output_tokens),
    )
    return response.text or ""

def embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT"):
    if not texts:
        return []
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [item.values for item in response.embeddings]

def embed_query(client, text):
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return response.embeddings[0].values

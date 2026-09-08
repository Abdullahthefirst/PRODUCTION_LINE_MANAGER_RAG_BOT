import time
from google import genai
from google.genai import types

# Stable production model requested for this project.
GENERATION_MODEL = "gemini-3.6-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

class GeminiTransientError(RuntimeError):
    pass

class GeminiModelUnavailableError(RuntimeError):
    pass

AUTH_MARKERS = (
    "api_key_invalid",
    "api key not valid",
    "invalid api key",
    "unauthenticated",
    "authentication",
    "unauthorized",
    "permission_denied",
    "401",
)

TRANSIENT_MARKERS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "resource_exhausted",
    "rate limit",
    "high demand",
    "unavailable",
    "temporarily unavailable",
    "timeout",
    "deadline exceeded",
)

MODEL_MARKERS = (
    "model not found",
    "model is not found",
    "not found for api version",
    "model unavailable",
    "model is unavailable",
    "404",
)

def create_client(api_key: str):
    return genai.Client(api_key=api_key)

def _text(exc: Exception) -> str:
    return str(exc).lower()

def is_auth_error(exc: Exception) -> bool:
    text = _text(exc)
    if any(x in text for x in TRANSIENT_MARKERS):
        return False
    # 403 can also mean access/permission rather than a malformed key. We only
    # treat it as auth if the response also carries a credential-style marker.
    if "403" in text and any(x in text for x in ("api key", "credential", "permission_denied")):
        return True
    return any(marker in text for marker in AUTH_MARKERS)

def is_transient_error(exc: Exception) -> bool:
    return any(marker in _text(exc) for marker in TRANSIENT_MARKERS)

def is_model_unavailable_error(exc: Exception) -> bool:
    text = _text(exc)
    if is_auth_error(exc) or is_transient_error(exc):
        return False
    return any(marker in text for marker in MODEL_MARKERS)

def _with_retries(fn, attempts=4, base_delay=1.0):
    last = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last = exc
            if is_auth_error(exc) or is_model_unavailable_error(exc):
                raise
            if not is_transient_error(exc) or attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
    raise last

def validate_key(api_key: str):
    """
    Validate credentials without making a generation call.
    Returns: (client, generation_model_available, model_names)

    A temporary 503 from the generation model therefore does not get mistaken
    for an invalid API key.
    """
    client = create_client(api_key)

    def list_models():
        return list(client.models.list())

    models = _with_retries(list_models, attempts=3, base_delay=0.6)
    names = []
    for model in models:
        name = getattr(model, "name", "") or ""
        names.append(name.removeprefix("models/"))

    model_available = GENERATION_MODEL in names
    return client, model_available, names

def generate_text(client, prompt: str, max_output_tokens: int = 1800) -> str:
    def call():
        return client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
            ),
        )

    try:
        response = _with_retries(call, attempts=4, base_delay=1.0)
    except Exception as exc:
        if is_model_unavailable_error(exc):
            raise GeminiModelUnavailableError(
                f"{GENERATION_MODEL} is not available to this API project/region right now."
            ) from exc
        if is_transient_error(exc):
            raise GeminiTransientError(
                f"{GENERATION_MODEL} is temporarily unavailable after several retries."
            ) from exc
        raise

    return (response.text or "").strip()

def embed_texts(client, texts, task_type="RETRIEVAL_DOCUMENT"):
    if not texts:
        return []

    def call():
        return client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )

    response = _with_retries(call, attempts=4, base_delay=0.8)
    return [item.values for item in response.embeddings]

def embed_query(client, text):
    def call():
        return client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[text],
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )

    response = _with_retries(call, attempts=4, base_delay=0.8)
    return response.embeddings[0].values

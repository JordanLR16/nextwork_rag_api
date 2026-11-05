from ..config import Settings

try:
    import ollama
except ImportError:
    ollama = None


def generate_completion(prompt: str, settings: Settings):
    """Generate using the configured model and optional Ollama host."""
    if ollama is None:
        raise RuntimeError("ollama is not installed. Install dependencies first.")
    options = {
        "model": settings.model_name,
        "prompt": prompt,
        "system": "Answer recipe questions using the supplied recipe context. Be concise and factual.",
        "options": {"temperature": 0, "num_predict": 256},
    }
    if settings.ollama_host:
        return ollama.Client(host=settings.ollama_host).generate(**options)
    return ollama.generate(**options)

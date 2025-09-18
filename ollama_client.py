import requests
import base64
from typing import Generator, Dict, Any, Optional

OLLAMA_BASE_URL = "http://localhost:11434"


def generate_text(prompt: str, model: str = "llama3:8b", base_url: Optional[str] = None) -> str:
    """Call Ollama /api/generate for text-only prompts and return the full response text."""
    url = (base_url or OLLAMA_BASE_URL).rstrip("/") + "/api/generate"
    resp = requests.post(url, json={
        "model": model,
        "prompt": prompt,
        "stream": False,
    })
    resp.raise_for_status()
    data = resp.json()
    # Some Ollama versions return {"response": "..."}
    return data.get("response", "")


def analyze_image(image_path: str, prompt: str, model: str = "llava:13b", base_url: Optional[str] = None) -> str:
    """Call Ollama /api/generate for a vision model using a local image and return the full response text."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    url = (base_url or OLLAMA_BASE_URL).rstrip("/") + "/api/generate"
    resp = requests.post(url, json={
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
    })
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")


class OllamaTextInference:
    """A tiny adapter to keep the existing interface (.create_completion) intact."""

    def __init__(self, model: str = "llama3:8b", base_url: Optional[str] = None):
        self.model = model
        self.base_url = base_url or OLLAMA_BASE_URL

    def create_completion(self, prompt: str) -> Dict[str, Any]:
        text = generate_text(prompt, model=self.model, base_url=self.base_url)
        return {"choices": [{"text": text}]}


class OllamaVLMInference:
    """A tiny adapter to keep the existing interface (._chat yielding deltas) intact.

    image_data_processing.get_text_from_generator expects a generator yielding
    dicts with a structure like {"choices": [{"delta": {"content": "..."}}]}.
    We provide a simple single-yield generator with the full content.
    """

    def __init__(self, model: str = "llava:13b", base_url: Optional[str] = None):
        self.model = model
        self.base_url = base_url or OLLAMA_BASE_URL

    def _chat(self, prompt: str, image_path: str) -> Generator[Dict[str, Any], None, None]:
        content = analyze_image(image_path, prompt, model=self.model, base_url=self.base_url)

        def _gen():
            yield {"choices": [{"delta": {"content": content}}]}
            return

        return _gen()

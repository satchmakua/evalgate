"""Local provider backed by Ollama (http://localhost:11434). Free; no API key."""

import time

import requests

from ..types import Completion
from .base import Provider


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, host="http://localhost:11434", timeout=180):
        self.host = host.rstrip("/")
        self.timeout = timeout

    def complete(self, model, messages, options=None):
        payload = {"model": model, "messages": messages, "stream": False}
        if options:
            payload["options"] = options
        started = time.time()
        resp = requests.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return Completion(
            text=data["message"]["content"],
            model=model,
            provider=self.name,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            latency_s=round(time.time() - started, 3),
        )

    def available(self):
        try:
            requests.get(f"{self.host}/api/tags", timeout=5).raise_for_status()
            return True
        except Exception:
            return False

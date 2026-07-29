from dataclasses import dataclass

from src.llm.client import generate

SMALL_MODEL = "qwen2.5:1.5b"
LARGE_MODEL = "qwen2.5:7b"


@dataclass
class OllamaStrategy:
    model: str = SMALL_MODEL
    temperature: float = 0.7
    timeout: int = 30

    def generate(self, prompt: str, system: str = "") -> str | None:
        return generate(self.model, prompt, system, self.temperature, timeout=self.timeout)


def get_strategy(use_large: bool = False) -> OllamaStrategy:
    if use_large:
        return OllamaStrategy(model=LARGE_MODEL, timeout=120)
    return OllamaStrategy(model=SMALL_MODEL, timeout=30)

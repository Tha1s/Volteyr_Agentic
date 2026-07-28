from typing import Protocol

from src.llm.client import generate

SMALL_MODEL = "qwen2.5:1.5b"
LARGE_MODEL = "qwen2.5:7b"


class LLMStrategy(Protocol):
    model: str
    temperature: float
    timeout: int

    def generate(self, prompt: str, system: str = "") -> str | None: ...


class SmallModelStrategy:
    model: str = SMALL_MODEL
    temperature: float = 0.7
    timeout: int = 30

    def generate(self, prompt: str, system: str = "") -> str | None:
        return generate(self.model, prompt, system, self.temperature, timeout=self.timeout)


class LargeModelStrategy:
    model: str = LARGE_MODEL
    temperature: float = 0.7
    timeout: int = 120

    def generate(self, prompt: str, system: str = "") -> str | None:
        return generate(self.model, prompt, system, self.temperature, timeout=self.timeout)


def get_strategy(use_large: bool = False) -> LLMStrategy:
    return LargeModelStrategy() if use_large else SmallModelStrategy()

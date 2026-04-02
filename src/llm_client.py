"""Provider-agnostic LLM abstraction, fake provider, and result parser."""

import re
from abc import ABC, abstractmethod
from typing import List

from src.models import Suggestion


class LLMError(Exception):
    """Raised when an LLM call fails."""


class ParseError(Exception):
    """Raised when LLM output cannot be parsed."""


class LLMClient(ABC):
    """Abstract LLM client interface."""

    @abstractmethod
    def chat(self, prompt: str) -> str:
        """Send a prompt and return the raw model text response."""


class FakeLLMClient(LLMClient):
    """Deterministic fake provider for testing."""

    def __init__(self, response_text: str):
        self._response = response_text

    def chat(self, prompt: str) -> str:
        return self._response


class DashScopeLLMClient(LLMClient):
    """DashScope/Qwen provider — credentials from config."""

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def chat(self, prompt: str) -> str:
        import dashscope
        messages = [{"role": "user", "content": prompt}]
        response = dashscope.Generation.call(
            api_key=self._api_key,
            model=self._model,
            messages=messages,
            result_format="message",
            enable_search=True,
        )
        if response.status_code != 200:
            raise LLMError(f"DashScope API error: status={response.status_code}")
        return response["output"]["choices"][0]["message"]["content"]


class OpenAILLMClient(LLMClient):
    """OpenAI-compatible provider — supports OpenAI API and compatible endpoints."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def chat(self, prompt: str) -> str:
        import sys
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        messages = [{"role": "user", "content": prompt}]
        stream = client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
        )
        chunks = []
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                chunks.append(delta.content)
        print()  # newline after streaming completes
        if not chunks:
            raise LLMError("OpenAI API returned empty content")
        return "".join(chunks)


def parse_suggestions(response_text: str, expected_money: int) -> List[Suggestion]:
    """Parse the %%...%% segment from LLM output into structured suggestions.

    Validates that the total amount equals expected_money.
    Raises ParseError on malformed output or incorrect totals.
    """
    # Extract %%...%% block
    print(f'response_text is {response_text}')
    result_match = re.search(r'%%(.*?)%%', response_text, re.DOTALL)
    if not result_match:
        raise ParseError("No %%...%% markers found in LLM output")

    block = result_match.group(1)

    # Parse each 【...】 entry
    pattern = r"【.*?\((.*?)\)，购买金额：(\d+)元】"
    matches = re.findall(pattern, block)

    if not matches:
        raise ParseError("No valid bet entries found inside %%...%% block")

    suggestions: List[Suggestion] = []
    for content, amount_str in matches:
        try:
            amount = int(amount_str)
        except ValueError as e:
            raise ParseError(f"Invalid amount '{amount_str}' in bet entry") from e
        suggestions.append({"play_content": content, "amount": amount})

    total = sum(s["amount"] for s in suggestions)
    if total != expected_money:
        raise ParseError(
            f"Total bet amount {total} does not equal expected {expected_money}"
        )

    return suggestions

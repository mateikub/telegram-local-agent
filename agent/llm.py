from __future__ import annotations

import base64
import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class LocalLLM:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, prompt: str, temperature: float = 0.2) -> str:
        return self.chat_messages(
            [{"role": "user", "content": prompt}],
            self.model,
            temperature,
        )

    def chat_with_image(
        self,
        prompt: str,
        image: bytes,
        mime_type: str = "image/jpeg",
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        encoded_image = base64.b64encode(image).decode("ascii")
        return self.chat_messages(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded_image}"
                            },
                        },
                    ],
                }
            ],
            model or self.model,
            temperature,
        )

    def chat_messages(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.2,
    ) -> str:
        endpoint = self.base_url + "/v1/chat/completions"
        body = json.dumps(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
        ).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=None) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"local LLM request failed: {details}") from error
        return data["choices"][0]["message"]["content"]

    def json(self, prompt: str) -> dict[str, Any]:
        content = self.chat(prompt)
        return extract_json(content)


def extract_json(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("local LLM did not return JSON")
    parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("local LLM did not return a JSON object")
    return parsed

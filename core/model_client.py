"""Smart Model Client for Auto'd.

Provides primary access to Google Gemini 2.5 Flash (1M TPM, 1M context, frontier reasoning)
with automated graceful fallback across Groq, Mistral, OpenRouter, and keyless Kilo AI.
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional
import requests

PROVIDER_ENDPOINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "kilo": "https://api.kilo.ai/api/gateway/chat/completions",
}


def _clean_json_text(text: str) -> str:
    """Strip markdown fences and whitespace from model responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def repair_json(text: str) -> Dict[str, Any]:
    """Robustly parse JSON, repairing common unescaped characters if needed."""
    cleaned = _clean_json_text(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract outermost JSON object or array
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        # Common LLM issue: unescaped control characters or trailing commas
        fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
        fixed = re.sub(r"[\x00-\x1f]", lambda m: f"\\u{ord(m.group(0)):04x}", fixed)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse model response into valid JSON: {cleaned[:200]}...")


class SmartModelClient:
    """Frontier LLM client tailored for complex code and architecture synthesis."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            default_config = os.path.join(os.path.dirname(__file__), "..", "config.json")
            if os.path.exists(default_config):
                with open(default_config, "r", encoding="utf-8") as f:
                    self.config = json.load(f)

        self.primary_model = self.config.get("primary_model", {
            "provider": "gemini",
            "model": "gemini-2.5-flash"
        })
        self.fallback_models = self.config.get("fallback_models", [
            {"provider": "groq", "model": "llama-3.3-70b-versatile"},
            {"provider": "mistral", "model": "codestral-latest"},
            {"provider": "kilo", "model": "nvidia/nemotron-3-ultra-550b-a55b:free"},
        ])

    def get_api_key(self, provider: str) -> str:
        """Resolve API keys from environment variables."""
        if provider == "gemini":
            return os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
        if provider == "groq":
            return os.environ.get("GROQ_API_KEY", "")
        if provider == "mistral":
            return os.environ.get("LLM3_API_KEY") or os.environ.get("MISTRAL_API_KEY", "")
        if provider == "openrouter":
            return os.environ.get("LLM2_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
        if provider == "kilo":
            return "kilo-anonymous-free"
        return ""

    def _call_gemini(self, model: str, api_key: str, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        url = PROVIDER_ENDPOINTS["gemini"].format(model=model, key=api_key)
        contents = [{"role": "user", "parts": [{"text": user_prompt}]}]
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.config.get("generation", {}).get("temperature", 0.35),
                "maxOutputTokens": self.config.get("generation", {}).get("max_output_tokens", 8192),
            }
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"

        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=body, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned 0 candidates: {data}")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts)

    def _call_openai_compatible(
        self,
        endpoint: str,
        model: str,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool,
    ) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else "",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.config.get("generation", {}).get("temperature", 0.35),
            "max_tokens": self.config.get("generation", {}).get("max_output_tokens", 8192),
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"{endpoint} error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"Empty choices from {endpoint}: {data}")
        return choices[0].get("message", {}).get("content", "")

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        json_mode: bool = False,
    ) -> str:
        """Call the primary smart model with rapid fallback to resilient tiers."""
        candidates = [self.primary_model] + self.fallback_models
        errors = []

        for candidate in candidates:
            provider = candidate.get("provider", "")
            model = candidate.get("model", "")
            api_key = self.get_api_key(provider)

            # Skip if provider requires API key and none is set (unless keyless like Kilo)
            if provider != "kilo" and not api_key:
                continue

            try:
                print(f"[Auto'd] Querying {provider} ({model})...")
                if provider == "gemini":
                    return self._call_gemini(model, api_key, system_prompt, user_prompt, json_mode)
                endpoint = PROVIDER_ENDPOINTS.get(provider)
                if endpoint:
                    return self._call_openai_compatible(
                        endpoint, model, api_key, system_prompt, user_prompt, json_mode
                    )
            except Exception as e:
                err_msg = f"{provider}/{model}: {e}"
                print(f"[Auto'd] Warning: {err_msg}. Falling back to next tier...")
                errors.append(err_msg)
                time.sleep(1)

        raise RuntimeError(f"All LLM tiers exhausted in Auto'd model client: {'; '.join(errors)}")

    def generate_json(
        self,
        user_prompt: str,
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        """Generate structured JSON response guaranteed to parse."""
        raw = self.generate(user_prompt=user_prompt, system_prompt=system_prompt, json_mode=True)
        return repair_json(raw)

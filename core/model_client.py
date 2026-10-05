"""Smart Model Client for Auto'd.

Primary access to Groq (fast, reliable permanent-free tier) with automated graceful
fallback across a pool of permanent-free-tier, OpenAI-compatible providers:
NVIDIA NIM, Mistral, OpenRouter, Hugging Face, ModelScope, Z.AI, LLM7.io, Cohere,
GitHub Models, Cloudflare Workers AI, and keyless Kilo AI.

Google Gemini has been removed.
"""

from typing import Any, Dict, Optional
import json
import os
import re
import time

import requests

# OpenAI-compatible chat-completions endpoints. Cloudflare is resolved separately
# because its URL embeds the account id (see _endpoint).
PROVIDER_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "nvidia": "https://integrate.api.nvidia.com/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "huggingface": "https://router.huggingface.co/v1/chat/completions",
    "modelscope": "https://api-inference.modelscope.cn/v1/chat/completions",
    "zai": "https://api.z.ai/api/paas/v4/chat/completions",
    "llm7": "https://api.llm7.io/v1/chat/completions",
    "cohere": "https://api.cohere.ai/compatibility/v1/chat/completions",
    "github_models": "https://models.github.ai/inference/chat/completions",
    "kilo": "https://api.kilo.ai/api/gateway/chat/completions",
}

# Environment variables that can supply each provider's key (first non-empty wins).
PROVIDER_KEY_ENV = {
    "groq": ("GROQ_API_KEY",),
    "nvidia": ("NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY"),
    "mistral": ("LLM3_API_KEY", "MISTRAL_API_KEY"),
    "openrouter": ("LLM2_API_KEY", "OPENROUTER_API_KEY"),
    "huggingface": ("HF_TOKEN", "HUGGINGFACE_API_KEY"),
    "modelscope": ("MODELSCOPE_API_KEY",),
    "zai": ("ZAI_API_KEY", "ZHIPU_API_KEY"),
    "llm7": ("LLM7_API_KEY",),
    "cohere": ("COHERE_API_KEY",),
    "github_models": ("GITHUB_MODELS_TOKEN", "MODELS_TOKEN"),
    "cloudflare": ("CLOUDFLARE_API_KEY", "CLOUDFLARE_API_TOKEN"),
}

# Default fallback chain (used when config.json has no fallback_models).
DEFAULT_FALLBACKS = [
    {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b"},
    {"provider": "mistral", "model": "codestral-latest"},
    {"provider": "openrouter", "model": "openrouter/free"},
    {"provider": "huggingface", "model": "Qwen/Qwen2.5-72B-Instruct"},
    {"provider": "modelscope", "model": "Qwen/Qwen3-235B-A22B-Instruct-2507"},
    {"provider": "zai", "model": "glm-4.7-flash"},
    {"provider": "llm7", "model": "default"},
    {"provider": "cohere", "model": "command-r-plus"},
    {"provider": "github_models", "model": "openai/gpt-4o-mini"},
    {"provider": "cloudflare", "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast"},
    {"provider": "kilo", "model": "nvidia/nemotron-3-ultra-550b-a55b:free"},
]


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
        """Initialize the client from config.json (or a supplied path)."""
        self.config: Dict[str, Any] = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            default_config = os.path.join(os.path.dirname(__file__), "..", "config.json")
            if os.path.exists(default_config):
                with open(default_config, "r", encoding="utf-8") as f:
                    self.config = json.load(f)

        self.primary_model = self.config.get("primary_model", {
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
        })
        self.fallback_models = self.config.get("fallback_models", list(DEFAULT_FALLBACKS))

    def get_api_key(self, provider: str) -> str:
        """Resolve a provider's API key from the environment (first non-empty wins)."""
        if provider == "kilo":
            # Keyless: works anonymously (an optional KILO_API_KEY raises limits).
            return os.environ.get("KILO_API_KEY") or "kilo-anonymous-free"
        for env_name in PROVIDER_KEY_ENV.get(provider, ()):
            value = os.environ.get(env_name, "")
            if value:
                return value
        return ""

    def _endpoint(self, provider: str) -> str:
        """Return the chat-completions endpoint for a provider.

        Cloudflare's URL embeds the account id, so it is built here rather than in
        PROVIDER_ENDPOINTS; it returns "" (provider skipped) when the id is missing.
        """
        if provider == "cloudflare":
            account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
            if not account_id:
                return ""
            return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
        return PROVIDER_ENDPOINTS.get(provider, "")

    def _call_openai_compatible(
        self,
        endpoint: str,
        model: str,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool,
    ) -> str:
        """POST a chat completion to an OpenAI-compatible endpoint."""
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
        """Call the primary model with rapid fallback across the free-tier pool."""
        candidates = [self.primary_model] + self.fallback_models
        errors = []

        for candidate in candidates:
            provider = candidate.get("provider", "")
            model = candidate.get("model", "")
            api_key = self.get_api_key(provider)
            endpoint = self._endpoint(provider)

            # Skip providers that need a key we don't have, or whose endpoint
            # can't be resolved (e.g. Cloudflare without an account id).
            if provider != "kilo" and not api_key:
                continue
            if not endpoint:
                continue

            try:
                print(f"[Auto'd] Querying {provider} ({model})...")
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

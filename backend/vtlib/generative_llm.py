import json
import math
import os
import re
import time
from typing import List, Optional

import litellm
from litellm import completion, embedding, image_generation

from vtutils.misc import resolve_project_file_path
from vtutils.vtlogger import getLog

# silence litellm's own logging unless needed
litellm.suppress_debug_info = True

# TODO > replace old generative_llm.py with this new one and remove old one


# map of known provider prefixes used by litellm
_PROVIDER_PREFIXES = {
    "openai":    "",              # gpt-4o-mini → gpt-4o-mini
    "anthropic": "anthropic/",    # claude-3-… → anthropic/claude-3-…
    "gemini":    "gemini/",       # gemini-1.5-flash → gemini/gemini-1.5-flash
    "vertexai":  "vertex_ai/",    # gemini-2.5-flash → vertex_ai/gemini-2.5-flash
}


class GenerativeLLM:
    """Unified LLM wrapper powered by litellm.

    Accepts a configuration dict with ``env_config`` containing API keys::

        configuration["env_config"] = {
            "openai":    {"apiKey": "sk-..."},
            "gemini":    {"apiKey": "AIza..."},
            "anthropic": {"apiKey": "sk-ant-..."},
        }

    Any model string accepted by litellm can be passed to ``call()``.
    Short-hand names (e.g. ``"gpt-4o-mini"``, ``"claude-sonnet-4-20250514"``,
    ``"gemini-1.5-flash"``) are auto-prefixed for litellm.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, configuration: dict):

        self.vtlog = getLog("genai")

        # set API keys as env vars so litellm picks them up
        self.gemini_key    = configuration.get("GOOGLE_GENAI_APIKEY") or ""
        self.openai_key    = configuration.get("OPENAI_APIKEY") or ""
        self.anthropic_key = configuration.get("ANTHROPIC_API_KEY") or ""

        self.vertexai_key = configuration.get("VERTEXAI_APIKEY") or ""

        self.google_sa_json = configuration.get("GOOGLE_SA") or None
        self.vertex_credentials_json = None
        if self.google_sa_json:
            json_file_path = resolve_project_file_path(
                self.google_sa_json.get("json_file")
            )
            if json_file_path and os.path.isfile(json_file_path):
                with open(json_file_path, "r") as file:
                    vertex_credentials = json.load(file)
                    self.vertex_credentials_json = json.dumps(vertex_credentials)
            else:
                self.vtlog.error(
                    "google_sa_file_not_found",
                    json_file=self.google_sa_json.get("json_file"),
                    resolved_path=json_file_path,
                )
        

        # # sets the keys as environment variables for litellm to use
        # if openai_key:
        #     os.environ.setdefault("OPENAI_APIKEY", openai_key)
        # if gemini_key:
        #     os.environ.setdefault("GEMINI_API_KEY", gemini_key)
        # if anthropic_key:
        #     os.environ.setdefault("ANTHROPIC_API_KEY", anthropic_key)

    # ── public API ───────────────────────────────────────────────────────────


    def get_models(
        self,
        provider: Optional[str] = None,
        grouped: bool = False,
        check_provider_endpoint: bool = False,
    ):
        """Return provider-aware model lists.

        Args:
            provider: One of openai, gemini, vertexai, anthropic.
                If set, returns a list only for that provider.
            grouped: If True, returns a dict grouped by provider.
            check_provider_endpoint: If True, ask provider APIs via LiteLLM when possible.
                Falls back to LiteLLM's local provider model catalog on failure.
        """
        supported = ["openai", "gemini", "vertexai", "anthropic"]

        if provider:
            normalized_provider = self._normalize_provider_name(provider)
            if normalized_provider not in supported:
                self.vtlog.error("unsupported_provider_for_model_list", provider=provider)
                return []
            return self._get_models_for_provider(
                normalized_provider, check_provider_endpoint=check_provider_endpoint
            )

        by_provider = {
            p: self._get_models_for_provider(
                p, check_provider_endpoint=check_provider_endpoint
            )
            for p in supported
        }

        if grouped:
            return by_provider

        # backward-compatible: flattened unique list
        all_models = []
        for p in supported:
            all_models.extend(by_provider[p])
        return sorted(set(all_models))

    def call(self, message_list: list, *,
             tools_list: list = None,
             llm_model: str = None,
             temperature: float = 0.1,
             response_format: str = "json",
             max_tokens: int = None,
             reasoning_effort: str = None,
            logprobs: bool = False,
             retry_count: int = 0) -> tuple:
        """Send a chat completion via litellm. Returns (response, meta).

        ``response_format`` can be ``"json"`` or ``"text"``.
        """
        model = self._resolve_model(llm_model or self.DEFAULT_MODEL)

        try:
            params: dict = {
                "model": model,
                "messages": message_list,
            }

            api_key = self._api_key_for_model(model)
            if api_key:
                params["api_key"] = api_key

            # temperature (some reasoning models ignore it)
            if temperature is not None and not model.startswith(("o5", "gpt-5")):
                params["temperature"] = temperature

            if max_tokens:
                params["max_tokens"] = max_tokens

            # json mode
            if response_format == "json":
                params["response_format"] = {"type": "json_object"}

            # tools
            if tools_list:
                params["tools"] = tools_list
                params["tool_choice"] = "auto"
            
            # vertexai authenticates with credentials
            if model.startswith("vertex_ai/") and self.vertex_credentials_json:
                params["vertex_credentials"] = self.vertex_credentials_json
                params["vertex_location"] = "global" # "us-central1"  # or "europe-west1", etc. - this is required for reasoning_effort to work with vertex_ai models

            # vertex_ai_location

            # reasoning effort (o-series / gpt-5)
            # this param needs to be added depending on the model capabilities, otherwise it can cause errors
            if reasoning_effort and model.startswith(("o4", "gpt-5")):
                params["reasoning_effort"] = reasoning_effort

            if reasoning_effort and model.startswith("vertex_ai/"):
                # can be low or high or minimal, low, medium, or high (gemini 3 flash)
                params["thinking_level"] = reasoning_effort
                
            # logprobs params are only supported by some models, so we add them conditionally
            if logprobs and (model.startswith("o3") or model.startswith("gpt-4o")):
                # this works only when response schema is simple?
                # response_schema = {"type": "STRING", "enum": ["Positive", "Negative", "Neutral"]}
                params["logprobs"] = True  # default is False
                params["top_logprobs"] = logprobs # get logprobs for top 5 tokens [1-20]
                """
                Prompt must be like this. Must answer with 0,1,2,3 or A,B,C,D according to options. Text only short.
                "Based on the email above, choose the best category ID from the list:
                [List of 1-10 with definitions]

                Category ID:"

                TODO > also set
                max_tokens: 1
                temperature: 0
                """


            # this is actually the call to litellm
            response = completion(**params)

            if not response:
                self.vtlog.error("no_response", model=model)
                return None, {"tokens": 0}

            response_message = response.choices[0].message.content

            # token usage
            usage = getattr(response, "usage", None)
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0
            meta = {"tokens": total_tokens, "model": model}
            if logprobs:
                meta["logprobs"] = self._extract_logprobs(response.choices[0])

            # parse json if requested
            if response_format == "json" and isinstance(response_message, str):
                response_message = self._parse_json(response_message)

            return response_message, meta

        except Exception as e:
            return self._handle_error(
                e, message_list, tools_list, model, temperature,
                response_format, max_tokens, reasoning_effort, retry_count,
            )

    # keep backward-compat aliases
    def call_openai_tools(self, message_list, tools_list=None,
                          llm_model="gpt-4o-mini", temperature=0.1,
                          response_format="json", retry_count=0,
                          reasoning_effort=None):
        return self.call(message_list, tools_list=tools_list,
                         llm_model=llm_model, temperature=temperature,
                         response_format=response_format,
                         reasoning_effort=reasoning_effort,
                         retry_count=retry_count)

    def get_embeddings(self, input_message: str,
                       model: str = "text-embedding-3-small"):
        """Return embedding vector via litellm."""
        try:
            input_message = input_message.replace("\n", " ").replace("\r", "")
            resolved_model = self._resolve_model(model)
            params = {
                "model": resolved_model,
                "input": [input_message],
            }
            api_key = self._api_key_for_model(resolved_model)
            if api_key:
                params["api_key"] = api_key

            if model.startswith("vertex_ai/") and self.vertex_credentials_json:
                params["vertex_credentials"] = self.vertex_credentials_json
                params["vertex_location"] = "global" # "us-central1"  # or "europe-west1", etc. - this is required for reasoning_effort to work with vertex_ai models
                
            # this is the call to embedding endpoint in litellm
            # can also have api_key, api_base here
            response = embedding(**params)
            return response.data[0]["embedding"]
        except Exception as e:
            self.vtlog.error("embedding_error", exc=e, model=model,
                             input_data=input_message[:200])
            return None

    def generate_image(self, prompt: str, *,
                       model: str = "gpt-image-1",
                       size: str = "1024x1024",
                       quality: str = "auto",
                       n: int = 1) -> tuple:
        """Generate an image via litellm. Returns (b64_json_or_url, meta).

        The response contains either a base64-encoded image or a URL
        depending on the provider.
        """
        resolved_model = self._resolve_model(model)
        try:
            params = {
                "prompt": prompt,
                "model": resolved_model,
                "n": n,
                "size": size,
                "quality": quality,
            }
            api_key = self._api_key_for_model(resolved_model)
            if api_key:
                params["api_key"] = api_key

            response = image_generation(**params)

            if not response or not response.data:
                self.vtlog.error("no_image_response", model=resolved_model)
                return None, {"error": "No image returned"}

            image_data = response.data[0]
            result = {
                "b64_json": getattr(image_data, "b64_json", None),
                "url": getattr(image_data, "url", None),
                "revised_prompt": getattr(image_data, "revised_prompt", None),
            }
            return result, {"model": resolved_model}
        except Exception as e:
            self.vtlog.error("image_generation_error", exc=e,
                             model=resolved_model, prompt=prompt[:200])
            return None, {"error": str(e)}

    # ── internals ────────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_model(model: str) -> str:
        """Add litellm provider prefix if the model name is bare."""
        if "/" in model:
            return model  # already prefixed (e.g. anthropic/claude-…)

        if model.startswith(("gpt-", "o1", "o3", "o4")):
            return model  # openai models don't need prefix
        if model.startswith("claude"):
            return f"anthropic/{model}"
        if model.startswith("gemini"):
            return f"gemini/{model}"

        return model  # unknown → pass through

    @staticmethod
    def _provider_for_model(model: str):
        if not model:
            return None

        if model.startswith("models/gemini"):
            return "gemini"

        if "/" in model:
            provider_prefix = model.split("/", 1)[0]
            if provider_prefix in _PROVIDER_PREFIXES:
                return provider_prefix

        if model.startswith("claude"):
            return "anthropic"
        if model.startswith("gemini"):
            return "gemini"
        if model.startswith("vertex_ai"):
            return "vertexai"
        if model.startswith(("gpt-", "o1", "o3", "o4", "o5", "text-embedding-")):
            return "openai"

        return None

    @staticmethod
    def _normalize_provider_name(provider: str) -> Optional[str]:
        if not provider:
            return None
        p = provider.strip().lower()
        aliases = {
            "vertex_ai": "vertexai",
            "vertexai": "vertexai",
            "google": "gemini",
            "google_genai": "gemini",
        }
        return aliases.get(p, p)

    @staticmethod
    def _to_litellm_provider_name(provider: str) -> str:
        return "vertex_ai" if provider == "vertexai" else provider

    @staticmethod
    def _normalize_model_name_for_provider(provider: str, model_name: str) -> str:
        model_name = (model_name or "").strip()
        if not model_name:
            return ""

        # preserve already-prefixed or special gemini "models/..." naming
        if "/" in model_name:
            if provider == "openai":
                return model_name
            if provider == "gemini" and model_name.startswith("models/"):
                return model_name
            if provider == "vertexai" and model_name.startswith("models/"):
                return f"vertex_ai/{model_name}"

            provider_prefix = {
                "anthropic": "anthropic/",
                "gemini": "gemini/",
                "vertexai": "vertex_ai/",
            }.get(provider)
            if provider_prefix and model_name.startswith(provider_prefix):
                return model_name
            if provider_prefix:
                return provider_prefix + model_name
            return model_name

        prefix = _PROVIDER_PREFIXES.get(provider, "")
        return f"{prefix}{model_name}" if prefix else model_name

    def _list_provider_models_from_litellm(
        self, provider: str, check_provider_endpoint: bool
    ) -> List[str]:
        litellm_provider = self._to_litellm_provider_name(provider)
        api_key = self._api_key_for_provider(provider)

        models = litellm.get_valid_models(
            custom_llm_provider=litellm_provider,
            check_provider_endpoint=check_provider_endpoint,
            api_key=api_key,
        )
        return models or []

    def _list_provider_models_from_catalog(self, provider: str) -> List[str]:
        litellm_provider = self._to_litellm_provider_name(provider)
        provider_models = litellm.models_by_provider.get(litellm_provider, [])
        if isinstance(provider_models, (set, tuple)):
            provider_models = list(provider_models)
        return provider_models or []

    def _get_models_for_provider(
        self, provider: str, check_provider_endpoint: bool = False
    ) -> List[str]:
        models = []
        try:
            models = self._list_provider_models_from_litellm(
                provider, check_provider_endpoint=check_provider_endpoint
            )
        except Exception as e:
            self.vtlog.error(
                "provider_model_list_error",
                provider=provider,
                check_provider_endpoint=check_provider_endpoint,
                exc=e,
            )

        # fallback to local LiteLLM model catalog
        if not models:
            models = self._list_provider_models_from_catalog(provider)

        normalized = [
            self._normalize_model_name_for_provider(provider, m) for m in models
        ]
        return sorted({m for m in normalized if m})

    def _api_key_for_model(self, model: str):
        provider = self._provider_for_model(model)
        if provider == "openai":
            return self.openai_key or None
        if provider == "gemini":
            return self.gemini_key or None
        if provider == "vertexai":
            return self.vertexai_key or None
        if provider == "anthropic":
            return self.anthropic_key or None
        return None

    def _api_key_for_provider(self, provider: str):
        if provider == "openai":
            return self.openai_key or None
        if provider == "gemini":
            return self.gemini_key or None
        if provider == "vertexai":
            return self.vertexai_key or None
        if provider == "anthropic":
            return self.anthropic_key or None
        return None

    @staticmethod
    def _extract_logprobs(choice) -> Optional[dict]:
        """Normalize LiteLLM/OpenAI logprobs into token -> probability mappings."""
        choice_logprobs = getattr(choice, "logprobs", None)
        content = getattr(choice_logprobs, "content", None) or []
        if not content:
            return None

        tokens = []
        for token_info in content:
            token_logprob = getattr(token_info, "logprob", None)
            top_logprobs = getattr(token_info, "top_logprobs", None) or []

            tokens.append({
                "token": getattr(token_info, "token", None),
                "logprob": token_logprob,
                "probability": math.exp(token_logprob) if token_logprob is not None else None,
                "top_logprobs": {
                    item.token: math.exp(item.logprob)
                    for item in top_logprobs
                    if getattr(item, "token", None) is not None and getattr(item, "logprob", None) is not None
                },
            })

        return {
            "tokens": tokens,
            "first_token_top_logprobs": tokens[0]["top_logprobs"],
        }

    def _parse_json(self, text: str):
        """Try to parse JSON from response text."""
        try:
            # we might be sending prompt like this and getting response like this, so we need to clean it before parsing
            if isinstance(text, str):
                if text.startswith("```json"):
                    text = text[7:].strip()
                if text.startswith("```"):
                    text = text[3:].strip()
                if text.endswith("```"):
                    text = text[:-3].strip()

            s = re.sub(r"(?m)(?:\r?\n[ \t]*){3,}", "\n", text)
            return json.loads(s)
        except Exception as exc:
            self.vtlog.error("no_valid_json_response", exc=exc,
                             response_message=text[:500])
            return text

    def _handle_error(self, e, message_list, tools_list, model,
                      temperature, response_format, max_tokens,
                      reasoning_effort, retry_count) -> tuple:
        """Unified error handling with exponential-backoff retry."""
        status_code = getattr(e, "status_code", None) or getattr(e, "code", None)
        error_message = getattr(e, "message", str(e))
        first_msg = (message_list[0]["content"][:100]
                     if message_list else "")

        # retry on 500 up to 3 times
        if status_code == 500 and retry_count < 3:
            self.vtlog.debug("llm_retry", model=model,
                             status_code=status_code, exc=e,
                             message_list=first_msg,
                             retry_count=retry_count)
            time.sleep(2 ** retry_count)
            return self.call(
                message_list, tools_list=tools_list,
                llm_model=model, temperature=temperature,
                response_format=response_format,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
                retry_count=retry_count + 1,
            )

        self.vtlog.error("llm_error", model=model,
                         status_code=status_code, exc=e,
                         message_list=first_msg)
        return None, {"tokens": 0,
                      "error": f"{type(e).__name__}: {status_code} - {error_message}"}

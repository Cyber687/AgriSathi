"""
AgriSathi - Local LLM Service

Connects the AgriSathi backend to a locally running
llama.cpp server using its OpenAI-compatible API.

Model:
    sarvam-1-v0.5-Q8_0.gguf

Default server:
    http://127.0.0.1:8080

This module does not make agricultural recommendations
authoritative. All generated responses must pass through
the AgriSathi safety and verification pipeline.
"""

import json
import urllib.error
import urllib.request
from typing import Optional


class LLMService:
    """
    Provides an interface to the local llama.cpp server.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        timeout: int = 180,
        max_tokens: int = 1024
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens

    # --------------------------------------------------
    # Internal HTTP request handler
    # --------------------------------------------------

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[dict] = None
    ) -> dict:
        """
        Sends an HTTP request to the llama.cpp server.
        """

        url = f"{self.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        body = None

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=body,
            headers=headers,
            method=method
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                response_text = response.read().decode("utf-8")

                if not response_text:
                    return {}

                return json.loads(response_text)

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode(
                "utf-8",
                errors="replace"
            )

            raise RuntimeError(
                f"llama.cpp HTTP error {exc.code}: {error_body}"
            ) from exc

        except urllib.error.URLError as exc:
            raise ConnectionError(
                "Unable to connect to the llama.cpp server. "
                "Make sure llama-server is running at "
                f"{self.base_url}. Details: {exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise TimeoutError(
                "The llama.cpp server did not respond in time."
            ) from exc

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "The llama.cpp server returned an invalid JSON response."
            ) from exc

    # --------------------------------------------------
    # Check server availability
    # --------------------------------------------------

    def health_check(self) -> dict:
        """
        Checks whether the local inference server is available.

        Returns:
            A dictionary describing the server status.
        """

        try:
            self._request("/health")

            return {
                "status": "success",
                "message": "llama.cpp server is available.",
                "server_url": self.base_url
            }

        except (ConnectionError, RuntimeError, TimeoutError) as exc:
            return {
                "status": "error",
                "message": str(exc),
                "server_url": self.base_url
            }

    # --------------------------------------------------
    # Generate a response
    # --------------------------------------------------

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generates text using the local Sarvam model.

        Args:
            prompt:
                User prompt or input text.

            system_prompt:
                Instructions describing how the model
                should behave.

            temperature:
                Sampling temperature. Lower values generally
                produce more predictable responses.

            max_tokens:
                Maximum number of tokens to generate.

        Returns:
            Generated response as a string.

        Raises:
            ValueError:
                If the input or generation parameters are invalid.

            ConnectionError or RuntimeError:
                If the server cannot process the request.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(
                "The prompt must be a non-empty string."
            )

        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                "Temperature must be between 0.0 and 2.0."
            )

        token_limit = (
            max_tokens
            if max_tokens is not None
            else self.max_tokens
        )

        if not isinstance(token_limit, int) or token_limit < 1:
            raise ValueError(
                "max_tokens must be a positive integer."
            )

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": token_limit,
            "stream": False
        }

        response = self._request(
            endpoint="/v1/chat/completions",
            method="POST",
            payload=payload
        )

        choices = response.get("choices", [])

        if not choices:
            raise RuntimeError(
                "The model server returned no generated choices."
            )

        message = choices[0].get("message", {})
        generated_text = message.get("content", "")

        if not isinstance(generated_text, str):
            raise RuntimeError(
                "The model server returned an unexpected response format."
            )

        generated_text = generated_text.strip()

        if not generated_text:
            raise RuntimeError(
                "The model generated an empty response."
            )

        return generated_text

    # --------------------------------------------------
    # Generate a response from conversation messages
    # --------------------------------------------------

    def generate_chat(
        self,
        messages: list,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generates a response from a conversation history.

        Each message should contain:
            role: system, user, or assistant
            content: message text
        """

        if not isinstance(messages, list) or not messages:
            raise ValueError(
                "Messages must be a non-empty list."
            )

        for message in messages:
            if not isinstance(message, dict):
                raise ValueError(
                    "Each message must be a dictionary."
                )

            if message.get("role") not in {
                "system",
                "user",
                "assistant"
            }:
                raise ValueError(
                    "Each message must have a valid role."
                )

            if not isinstance(message.get("content"), str):
                raise ValueError(
                    "Each message must contain string content."
                )

        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                "Temperature must be between 0.0 and 2.0."
            )

        token_limit = (
            max_tokens
            if max_tokens is not None
            else self.max_tokens
        )

        if not isinstance(token_limit, int) or token_limit < 1:
            raise ValueError(
                "max_tokens must be a positive integer."
            )

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": token_limit,
            "stream": False
        }

        response = self._request(
            endpoint="/v1/chat/completions",
            method="POST",
            payload=payload
        )

        choices = response.get("choices", [])

        if not choices:
            raise RuntimeError(
                "The model server returned no generated choices."
            )

        generated_text = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )

        if not isinstance(generated_text, str):
            raise RuntimeError(
                "The model server returned an unexpected response format."
            )

        generated_text = generated_text.strip()

        if not generated_text:
            raise RuntimeError(
                "The model generated an empty response."
            )

        return generated_text
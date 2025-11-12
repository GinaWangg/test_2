import asyncio
import os
import json
from textwrap import dedent
from typing import Optional
from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletionMessageParam

API_VERSION_DEFAULT = '2024-02-01'   # 改成你專案的名稱

class GptClient:
    """Async client for Azure OpenAI GPT-4 models.
    
    This class manages connection to Azure OpenAI and provides methods for
    interacting with GPT-4 models with proper error handling and retry logic.
    """
    
    def __init__(
        self,
        api_version: str = API_VERSION_DEFAULT, 
        resource_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ) -> None:
        """Initialize GPT-4 client with Azure OpenAI credentials.
        
        Args:
            resource_endpoint: Azure OpenAI endpoint URL. If None, reads from
                MYAPP_GPT4O_RESOURCE_ENDPOINT environment variable.
            api_key: Azure OpenAI API key. If None, reads from
                MYAPP_GPT4O_API_KEY environment variable.
            default_model: Default model name to use. If None, reads from
                MYAPP_GPT4O_INTENTDETECT environment variable.
            api_version: Azure OpenAI API version. Defaults to '2024-02-01'.
        
        Raises:
            ValueError: If required credentials are not provided or found in
                environment.
        """
        self._resource_endpoint = (
            resource_endpoint or 
            os.getenv('MYAPP_GPT4O_RESOURCE_ENDPOINT', '')
        )
        self._api_key = api_key or os.getenv('MYAPP_GPT4O_API_KEY', '')
        self._default_model = (
            default_model or 
            os.getenv('MYAPP_GPT4O_INTENTDETECT', '')
        )
        self._api_version = api_version
        self._client: Optional[AsyncAzureOpenAI] = None
        self._validate_credentials()
        
    def _validate_credentials(self) -> None:
        """Validate that all required credentials are set.
        
        Raises:
            ValueError: If any required credential is missing.
        """
        if (not self._resource_endpoint or 
            not self._api_key or 
            not self._default_model):
            raise ValueError(
                "GPT-4 client requires MYAPP_GPT4O_API_KEY, "
                "MYAPP_GPT4O_RESOURCE_ENDPOINT, "
                "and MYAPP_GPT4O_INTENTDETECT to be set."
            )
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client connection.
        
        This should be called during application startup.
        """
        if self._client is not None:
            raise ValueError("Client is already initialized.")
            
        self._client = AsyncAzureOpenAI(
            azure_endpoint=self._resource_endpoint,
            api_key=self._api_key,
            api_version=self._api_version
        )

        print("GPT-4 client initialized successfully")
    
    async def close(self) -> None:
        """Close the Azure OpenAI client connection.
        
        This should be called during application shutdown.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None
            print("GPT-4 client closed successfully")
    
    def _to_json_format(self, x):
        """Convert string to JSON format."""

        if not isinstance(x, dict):
            try:
                x = json.loads(x.replace("jsonl", "").replace("```", "").replace("json", ""))
            except json.JSONDecodeError:
                return x
        return x

    
    async def _call(
        self,
        conversation: list[ChatCompletionMessageParam],
        timeout: float = 5.0,
        temperature: float = 0.0,
        model: Optional[str] = None,
        response_format={"type": "json_object"}
    ) -> dict:
        """Call GPT-4 with the provided conversation.
        
        This method implements retry logic with a single retry attempt on
        failure.
        
        Args:
            conversation: List of message dictionaries with 'role' and
                'content' keys.
            timeout: Request timeout in seconds. Defaults to 5.0.
            temperature: Sampling temperature (0.0-1.0). Defaults to 0.0 for
                deterministic output.
            model: Model name to use. If None, uses default model from
                initialization.
            response_format: Response format specification. Defaults to JSON
                object.
        
        Returns:
            The model's response content as a string.
        
        Raises:
            ValueError: If the client has not been initialized.
            WarningException: If the request fails after retry attempts.
        """
        if self._client is None:
            raise ValueError(
                "Client has not been initialized. Call `initialize()` first."
            )
        
        client = self._client
        model_name = model or self._default_model
        
        async def gpt_chat_completion():
            result = await client.chat.completions.create(
                model=model_name,
                messages=conversation,
                response_format=response_format,
                temperature=temperature,
            )
            return result.choices[0].message.content or ""

        try:
            response = await asyncio.wait_for(
                gpt_chat_completion(),
                timeout=timeout
            )
            return self._to_json_format(response)

        except asyncio.TimeoutError:
            print(f"GPT-4 call timed out after {timeout}s, retrying without "
                  f"timeout")
            response = await gpt_chat_completion()
            return self._to_json_format(response)

    async def call_with_prompts(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: float = 5.0,
        temperature: float = 0.0,
        model: Optional[str] = None
    ) -> dict:
        """Convenience method to call GPT-4 with system and user prompts.
        
        Args:
            system_prompt: System instruction for the model.
            user_prompt: User message content.
            timeout: Request timeout in seconds. Defaults to 5.0.
            temperature: Sampling temperature. Defaults to 0.0.
            model: Model name to use. If None, uses default model.
        
        Returns:
            The model's response content as a string.
        
        Raises:
            ValueError: If the client has not been initialized.
            WarningException: If the request fails after retry attempts.
        """
        
        conversation: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": dedent(system_prompt).strip()},
            {"role": "user", "content": dedent(user_prompt).strip()}
        ]
        
        return await self._call(
            conversation,
            timeout=timeout,
            temperature=temperature,
            model=model
        )

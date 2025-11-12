"""Google Translate client with lifespan management."""

from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from langid.langid import LanguageIdentifier, model
import base64
import json
import os


class GoogleTranslateClient:
    """Google Translate client for translation services."""

    def __init__(self):
        """Initialize Google Translate client.
        
        Raises:
            RuntimeError: If MYAPP_GOOGLE_GENIOTRANSLATE env var not set.
        """
        self._translate_client = None
        self._lang_identifier = None
        
        cred_b64 = os.getenv("MYAPP_GOOGLE_GENIOTRANSLATE")
        if not cred_b64:
            raise RuntimeError(
                "Missing env var: MYAPP_GOOGLE_GENIOTRANSLATE"
            )
        self._cred_b64 = cred_b64

    async def initialize(self) -> None:
        """Initialize translation client and language identifier."""
        info = json.loads(base64.b64decode(self._cred_b64))
        SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
        creds = service_account.Credentials.from_service_account_info(
            info
        ).with_scopes(SCOPES)
        self._translate_client = translate.Client(credentials=creds)
        
        self._lang_identifier = LanguageIdentifier.from_modelstring(
            model, 
            norm_probs=True
        )

    async def close(self) -> None:
        """Close client resources."""
        pass

    def translate_text(self, text: str, target: str = 'en') -> str:
        """Translate text to target language.
        
        Args:
            text: Text to translate.
            target: ISO 639-1 language code (default: 'en').
            
        Returns:
            Translated text string.
        """
        if isinstance(text, bytes):
            text = text.decode("utf-8")

        result = self._translate_client.translate(
            text, 
            target_language=target
        )
        return result.get('translatedText', text)

    def classify_language(self, text: str) -> tuple[str, float]:
        """Classify language of text.
        
        Args:
            text: Text to classify.
            
        Returns:
            Tuple of (language_code, confidence_probability).
        """
        return self._lang_identifier.classify(text)

"""Email translation handler."""

import html
import json
import re

from api_structure.core.timer import timed
from api_structure.src.clients.google_translate import GoogleTranslateClient
from api_structure.src.clients.gpt import GptClient


def _clean_text(query: str) -> str:
    """Clean HTML from text.

    Args:
        query: Text to clean.

    Returns:
        Cleaned text string.
    """
    clean_output = html.unescape(query)
    clean_output = re.sub(r"<div><br></div><div>", ", ", clean_output)
    clean_output = re.sub(r"\n|<br>|<div>|</div>", " ", clean_output)
    return clean_output


def _build_translate_prompt(user_input: str) -> list[dict]:
    """Build conversation for translation GPT.

    Args:
        user_input: Text to translate.

    Returns:
        List of conversation messages.
    """
    sys_prompt = """
You are a translator, user will provide a question, you don't have to understand question, just please translate the question into English and reply to en_question in jsonl format. If the question cannot be translated into English or has been English already, please fill in the original question.
Here are some knowledge you need to know
1. If user said Notebook have second screen or display controller, it is called "sreenPad"
2. Ignore bullet points and typo error from user input.
3. replace the word laptop by notebook and replace the word screen by display in your english sentence.
4. no question mark, no bullet points in your english sentence.
5. respond original question if you cannot translate the phrase.

Here are the output samples. Always respond with JSON format and answer in English.

1.question: 路由器的連線品質很差，要怎麼改善?"
jsonl sample:
{"en_question":"How to set up the network for a newly purchased router?"}

2.question: feel heat from vents"
jsonl sample:
{"en_question":"feel heat from vents"}

3.question: Error Code: 0x00000010"
jsonl sample:
{"en_question":"Error Code: 0x00000010"}
"""
    user_prompt = (
        "Please respond in JSONL format, and the en_question field should "
        "be filled with the question translated into English.\n"
        "If the question cannot be translated into English or has been "
        "English already, please fill in the original question.\n"
        f"The question is as follows: {user_input}."
    )

    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _handle_gpt_error_response(user_input: str) -> str:
    """Generate fallback response on GPT error.

    Args:
        user_input: Original input text.

    Returns:
        JSON string with original input.
    """
    return json.dumps({"en_question": user_input})


@timed(task_name="email_translate")
async def translate_to_english(
    gpt_client: GptClient,
    google_translate_client: GoogleTranslateClient,
    user_input: str,
) -> str:
    """Translate text to English using GPT and Google Translate.

    Args:
        gpt_client: Initialized GPT client.
        google_translate_client: Initialized Google Translate client.
        user_input: Text to translate.

    Returns:
        Translated English text.
    """
    # Step 1: Get GPT translation result
    conversation = _build_translate_prompt(user_input)
    try:
        result = await gpt_client.call_with_conversation(conversation)
    except Exception:
        result = _handle_gpt_error_response(user_input)

    # Step 2: Extract JSON response
    try:
        response = json.loads(result).get("en_question", user_input)
        response = response.replace("..", ".")
    except Exception:
        try:
            response = result.replace("..", ".")
        except Exception:
            response = user_input

    # Step 3: Check if English, otherwise use Google Translate
    is_en, prob = google_translate_client.classify_language(response)

    if (is_en == "en" and prob <= 0.8) or is_en != "en":
        response = google_translate_client.translate_text(response, "en")

    response = _clean_text(response)

    return response

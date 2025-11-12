"""Email split extraction handler."""

import json

from api_structure.core.timer import timed
from api_structure.src.clients.gpt import GptClient


def _build_split_prompt(email_context: str, lang: str) -> tuple[str, str]:
    """Build system and user prompts for email splitting.

    Args:
        email_context: Email content to split.
        lang: Language code for output.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    sys_prompt = """
You are an intelligent assistant whose task is to extract structured product-related information from customer emails. Your goal is to decompose the customer's message into standalone, self-contained sentences that clearly describe individual product issues or inquiries.

## Extraction Rules:
1. Write all extracted sentences in the language specified by the user in `{lang}`.
2. Output the result in a JSON object with keys formatted as `"extracted_sentenceN"` (e.g., `"extracted_sentence1"`, `"extracted_sentence2"`, ...).

---
## Extraction Priority
Always extract the following categories, even in long emails. Each item must be separated into clear, standalone sentences:

### High-Priority Categories:
- **Technical Support**  
  Product issues involving hardware/software, performance, drivers, power, charging, connectivity, display, BIOS, keyboard, etc.
- **Repair Consultation**  
  Service center lookup, repair status, repair applications, quotations, and complaints.
- **Warranty-Related**  
  Warranty policy, purchasing extended warranty, checking or updating warranty period.

---

## Sentence Structuring Rules

3. Each extracted sentence must be:
  - Self-contained and interpretable alone  
  - Include relevant product context if available  
  - Written in the specified output language (`{lang}`)

4. When multiple statements describe the same issue progression (e.g., symptom + attempted solution + result), merge them into a single, fluent sentence:

  Example (merge):  
  "いくつかのアプリが正常に動作しなくなり、再起動しても状況が変わらない状態です。"  
  Don't extract separately:  
  "幾つかのアプリが正常に動作しなくなっています。"  
  "再起動しても状況は変わりません。"

5. Do not split phrases that are:
  - Part of a cause-effect explanation  
  - Attempted solution followed by failure  
  - Symptom escalation

6. **Always speak from the customer's perspective.**  
   - Do **not** use third-person narration like `"The customer said..."` or `"The user wants..."`  
   - Use phrasing that reflects direct experience or intent  
     Examples:  
     `"Had the screen replaced at an ASUS center."`  
     `"Need to check warranty on the new display."`  
     `"Noticed the battery drains fast after the last update."`  
     Avoid:  
     `"The customer had their screen replaced..."`  
     `"The user is asking about..."`

---
## Sentence Simplification (Optional Refinement Phase)

7. After extraction, simplify and shorten the sentence when possible to make it more conversational and concise — **as long as the sentence remains self-contained and retains necessary product context**. Use everyday language where appropriate. Do not reduce clarity or introduce ambiguity.

Examples:
- Input: `I recently had the display of my ASUS TUF laptop replaced at an ASUS-authorized service center.`  
  Output: `My Gaming NB had the display replaced at an ASUS-authorized service center.`

- Input: `Although my laptop itself is out of warranty, I would like to confirm the warranty duration that applies to the newly replaced display.`  
  Output: `I need to confirm the warranty duration for the newly replaced display.`

---
## Trimming Strategy for Long Emails

8. If the email content would result in more than 5 extracted sentences:

  - Only retain sentences related to the high-priority categories above  
  - Among these, prefer descriptive and diagnostic statements (e.g., `"Windows reports code 43 with the GPU"`)
  - Omit customer self-action statements (e.g., `"I checked all drivers but none worked"`)

---

## Input Format:

The email context: `{email_context}`  
Provide the response in `"{lang}"` and structure it in JSON format as follows:

```json
{
  "extracted_sentence1": "...",
  "extracted_sentence2": "...",
  ...
}
"""
    user_prompt = (
        f"The email context:{email_context}.\n"
        f'Provide the response in "{lang}" and structure it in JSON format '
        "as described."
    )
    return sys_prompt, user_prompt


@timed(task_name="email_split")
async def generate_email_split(
    gpt_client: GptClient, email_content: str, lang: str
) -> dict:
    """Generate email split extraction.

    Args:
        gpt_client: Initialized GPT client.
        email_content: Email content to split.
        lang: Language code for output.

    Returns:
        Dictionary with extracted sentences.

    Raises:
        ValueError: If GPT response is invalid.
    """
    sys_prompt, user_prompt = _build_split_prompt(email_content, lang)
    conversation = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = await gpt_client.call_with_conversation(conversation)

    try:
        if response is None:
            raise ValueError("GPT response is None")
        result = json.loads(response)
        return result
    except Exception:
        # Retry once
        response = await gpt_client.call_with_conversation(conversation)
        result = json.loads(response)
        return result

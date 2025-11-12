"""Email summary generation handler."""

import json
from api_structure.core.timer import timed
from api_structure.src.clients.gpt import GptClient


def _build_summary_prompt(email_context: str) -> tuple[str, str]:
    """Build system and user prompts for email summarization.
    
    Args:
        email_context: Email content to summarize.
        
    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    sys_prompt = '''
Your objective is to summarize customers' inquiries. Below are some guidelines to follow:
1.Start by identifying the language used by the **CUSTOMERS FOR WRITING**, and use it as the summarized_in_this_language.(formatted as "xx-xx" e.g., "en-us" for American English)
2.Highlight specific segments pertinent to product issues, such as cases where notebooks fail to power on or display a blue screen.
3.Concisely summarize customers' inquiries using the language specified by summarized_in_this_language.
4.Avoid verbose, word-for-word descriptions.
5.Begin each summary with 'I' or 'My product' as the subject in the summarized_in_this_language.
6.Provide responses in JSON format.
7.If the content under [Problem Description] is too fragmented to extract meaningful sentences, return the original text as is in a single paragraph without breaking it down.

Example1:
email :"[Product Information]
Product Type: Premium PhoneProduct 

[Problem Description]
主旨: Overheating and Repair Inquiry
Hello ASUS Customer Service,
My ROG 3 tends to overheat after short usage and getting a CPU fan error message. I have been requesting the team to thoroughly check every part of my system for several months now. It is frustrating to have spent a significant amount of money on a system that is constantly crashing and hanging. I believe that with the specifications it has, these problems should not be occurring. I kindly request that my system be picked up and thoroughly checked for any issues with each and every part.
Thank you."
JSON format :{"summarize_in_this_language":"en-us","email_summary":"My ROG Phone 3 gets really hot after using it for a while and getting a CPU fan error message."}

Example2:
email :"[Product Information]
Product Type: 筆電

[Problem Description]
ប្រធាន: 我的電腦不能充電，可以怎麼辦?
另外我中文不太好，可以用英文回信給我嗎?"
JSON format :{"summarize_in_this_language":"zh-tw","email_summary":"我的電腦不能充電，用英文回信給我"}

Example3:
email :"Apply Date: 2024/09/25 20:22:08.698 (UTC Time)<br><br>[Información de contacto]<br>Apellido: Jorge Vasquez<br>Dirección de correo electrónico: shoxo94@gmail.com<br>Servicio técnico más cercano: Chile<br>Número de teléfono: 0<br><br>[Información de producto]<br>Tipo de producto: Gaming NB<br>Modelo de producto: FA617NT<br>Número de serie del producto: RANRKD006858413<br>Sistema operativo / firmware o versión del BIOS: Windows 11<br><br>[Descripción del problema]<br>please tell me ノートパソコンの画面が真っ暗になり、電源が入らなくなった場合はどうすればよいですか?"
JSON format :{"summarize_in_this_language":"ja-jp","email_summary":"ノートパソコンの画面が真っ暗で電源が入りません"}
'''
    user_prompt = f'''Kindly provide me with the 'summarize_in_this_language' and 'email_summary', and reply the language specified in 'summarize_in_this_language' for the output.
email:{email_context}
JSON format:'''
    return sys_prompt, user_prompt


async def _call_summary_gpt(
        gpt_client: GptClient,
        email_context: str,
        last_response: str = 'empty input',
        error_message: str = None
) -> str:
    """Call GPT for email summary.
    
    Args:
        gpt_client: Initialized GPT client.
        email_context: Email content to summarize.
        last_response: Previous response for retry.
        error_message: Error from previous attempt.
        
    Returns:
        GPT response string.
    """
    sys_prompt, user_prompt = _build_summary_prompt(email_context)

    if last_response == 'empty input':
        conversation = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
    else:
        if last_response is None:
            last_response = 'None'
        conversation = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_prompt},
            {'role': 'assistant', 'content': last_response},
            {
                'role': 'user',
                'content': (
                    f'Error message is : {error_message}. '
                    'Please correct and try again.'
                )
            }
        ]
    
    return await gpt_client.call_with_conversation(conversation)


def _parse_summary_response(response: str) -> tuple[str, str]:
    """Parse GPT summary response.
    
    Args:
        response: GPT response string.
        
    Returns:
        Tuple of (summary, language_code).
        
    Raises:
        ValueError: If response cannot be parsed.
    """
    try:
        response_json = json.loads(response)
        summary = response_json['email_summary']
        lang = response_json['summarize_in_this_language']
        return summary, lang
    except Exception:
        # Try cleaning response
        cleaned = response.replace("\\", " ")
        cleaned = cleaned.replace('```', '')
        cleaned = cleaned.replace('json', '')
        response_json = json.loads(cleaned)
        summary = response_json['email_summary']
        lang = response_json['summarize_in_this_language']
        return summary, lang


@timed(task_name="email_summary")
async def generate_email_summary(
        gpt_client: GptClient,
        email_content: str
) -> tuple[str, str]:
    """Generate email summary and detect language.
    
    Args:
        gpt_client: Initialized GPT client.
        email_content: Email content to summarize.
        
    Returns:
        Tuple of (summary, language_code).
        
    Raises:
        TimeoutError: If summary generation fails after retry.
    """
    response = await _call_summary_gpt(gpt_client, email_content)
    
    try:
        summary, lang = _parse_summary_response(response)
        return summary, lang
    except Exception as first_error:
        # Retry once
        retry_response = await _call_summary_gpt(
            gpt_client,
            email_content,
            last_response=response,
            error_message=str(first_error)
        )
        try:
            summary, lang = _parse_summary_response(retry_response)
            return summary, lang
        except Exception as second_error:
            raise TimeoutError(
                f'Error in generate_email_summary: {second_error}, '
                f'input: {email_content}'
            )

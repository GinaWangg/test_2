# import config # 跑單一檔案測試時候要導入環境變數
import json
try:
    from .call_gpt import call_gpt4o as call_gpt
except ImportError:
    from call_gpt import call_gpt4o as call_gpt
from langid.langid import LanguageIdentifier, model
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import base64
import html
import re
import os
# os.chdir("c:/Users/gina3_wang/OneDrive - ASUS/Folder/任務/20240103_email copilot/email_copilot")
'''
參考 patty 202411/4 在 AA - \\TP-TABLEAU-V05\DSTeam\Projects\202305_KB Chatbot\intent_vec\script\轉譯 
提供的程式
'''

model_google_translate = None

def initialize_google_translate():
    global model_google_translate
    if model_google_translate is None:
        model_google_translate = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        print('Google Translate Model Initialized (api1_v3)')

def handle_gpt_error_response(user_input):
    response = json.dumps(
        { "en_question": user_input }
    )
    return response

def clean_text(query):
    # Unescape HTML characters in the query
    clean_output = html.unescape(query)
    # Replace specific HTML sequences with a comma and a space
    clean_output = re.sub(r'<div><br></div><div>', ', ', clean_output)
    # Remove newline characters, <br>, <div>, and </div> from clean_output
    clean_output = re.sub(r'\n|<br>|<div>|</div>', ' ', clean_output)
    return clean_output

def translate_text(text: str, target='en') -> dict: 
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages

    Text can also be a sequence of strings, in which case this method will return 
    a sequence of results for each text.
    """
    cred_b64 = os.getenv("MYAPP_GOOGLE_GENIOTRANSLATE")
    if not cred_b64:
        raise RuntimeError("Missing env var: MYAPP_GOOGLE_GENIOTRANSLATE")

    
    info = json.loads(base64.b64decode(cred_b64))
    SCOPES = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    creds = service_account.Credentials.from_service_account_info(info).with_scopes(SCOPES)
    translate_client = translate.Client(credentials=creds)


    # Check if the input text is bytes, if so, decode it to utf-8
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    result = translate_client.translate(text, target_language=target)

    return result.get('translatedText')

async def gpt_translate(user_input=None):
    if model_google_translate is None:
        raise ValueError("Google Translate Model has not been initialized. Call `initialize_google_translate()` first.")

    messages = [
{'role':'system','content':'''
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
'''},
{"role": "user", 
"content": '''Please respond in JSONL format, and the en_question field should be filled with the question translated into English.
If the question cannot be translated into English or has been English already, please fill in the original question. 
The question is as follows: {}.'''.format(user_input)
            }]

    # Step1 - 取得 openai 轉譯結果
    try:
        result = await call_gpt(conversation = messages) 
    except:
        result = handle_gpt_error_response(user_input)
    
    # Step2 - 擷取JSON格式的回應
    try:
        response = json.loads(result).get('en_question').replace('..', '.')
    except:
        response = handle_gpt_error_response(user_input)
        try:
            response = result.replace('..','.')
        except:
            response = user_input
    
    # Step3 - 判斷是否為英文，若不是則進行Google翻譯
    is_en, prob = model_google_translate.classify(response)

    if (is_en == 'en' and prob <= 0.8) or is_en != 'en':
        response = translate_text(response, 'en')
    
    response = clean_text(response)
    
    return response

if __name__ == '__main__':
    from .call_gpt import initialize_client_gpt4o
    initialize_google_translate()
    initialize_client_gpt4o()
    import asyncio
    async def main():
        print(await gpt_translate('我的電腦開不了機'))
    asyncio.run(main())
    
    print('---- 測試google翻譯 ----')
    print(translate_text('我的電腦開不了機', 'en'))

# pip install google-genai ==1.11.0
from google import genai
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold
import os
import re
# os.chdir("c:/Users/gina3_wang/OneDrive - ASUS/Folder/任務/20240103_email copilot/email_copilot")
# import config # 跑單一檔案測試時候要導入環境變數

import os, base64, json
from google.oauth2 import service_account

cred_b64 = os.getenv("MYAPP_GEMINI_API_KEY")
if not cred_b64:
    raise RuntimeError("MYAPP_GEMINI_API_KEY not set")

info = json.loads(base64.b64decode(cred_b64))
scoped_creds = (
    service_account.Credentials
    .from_service_account_info(info)
    .with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
)


client = genai.Client(
      vertexai=True,
      project="genai-service",
      location="europe-central2",
      credentials=scoped_creds
  )


async def call_gemini(conversation):

    for message in conversation:
        if message.get('role') == "user":
            user_prompt = message.get('content')
        elif message.get('role') == "system":
            system_input = message.get('content')

    model = "gemini-2.0-flash-001"
    contents = [
    types.Content(
        role="user",
        parts=[
        types.Part.from_text(text=user_prompt),
        ]
    ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature = 1,
        top_p = 0.95,
        max_output_tokens = 8192,
        response_modalities = ["TEXT"],
        safety_settings = [
            types.SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            )
        ],
        system_instruction=[types.Part.from_text(text=system_input)],
    )

    response_ = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config
    )
    
    # 處理 markdown 格式的 ```json ... ```，只取出純 JSON 內容
    text = response_.text if response_.text else ""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return text




# system_input = '你是一個聊天機器人'
# user_prompt = '介紹你自己'


# generate_content_config = types.GenerateContentConfig(
#     temperature = 1,
#     top_p = 0.95,
#     max_output_tokens = 8192,
#     response_modalities = ["TEXT"],
#     safety_settings = [types.SafetySetting(
#     category="HARM_CATEGORY_HATE_SPEECH",
#     threshold="OFF"
#     ),types.SafetySetting(
#     category="HARM_CATEGORY_DANGEROUS_CONTENT",
#     threshold="OFF"
#     ),types.SafetySetting(
#     category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
#     threshold="OFF"
#     ),types.SafetySetting(
#     category="HARM_CATEGORY_HARASSMENT",
#     threshold="OFF"
#     )],
    
#     system_instruction=[types.Part.from_text(text=system_input)],
# )
# response = client.models.generate_content(
#     model=model,
#     contents=contents,
#     config=generate_content_config
# )


# response_ = await client.aio.models.generate_content(
#     model=model,
#     contents=contents,
#     config=generate_content_config
# )


# print(response.text)

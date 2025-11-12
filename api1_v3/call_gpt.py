# %%
from openai import AsyncAzureOpenAI
import os
import time
import asyncio
# os.chdir("c:/Users/gina3_wang/OneDrive - ASUS/Folder/任務/20240103_email copilot/email_copilot")
# import config # 跑單一檔案測試時候要導入環境變數


client_gpt_4o = None

RESOURCE_ENDPOINT_ : str = os.getenv('MYAPP_GPT4O_RESOURCE_ENDPOINT')# type: ignore[assignment]
API_KEY_ = os.getenv('MYAPP_GPT4O_API_KEY')
intentDetect_ : str = os.getenv('MYAPP_GPT4O_INTENTDETECT')# type: ignore[assignment]
if RESOURCE_ENDPOINT_ is None or API_KEY_ is None or intentDetect_ is None:
    raise ValueError("Environment variables MYAPP_GPT4O_API_KEY, MYAPP_GPT4O_RESOURCE_ENDPOINT, and MYAPP_GPT4O_INTENTDETECT must be set.")

def initialize_client_gpt4o():
    global client_gpt_4o
    if client_gpt_4o is None:
        endpoint = RESOURCE_ENDPOINT_
        key = API_KEY_
        client_gpt_4o = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version='2024-02-01'
        )


async def call_gpt4o(conversation, time_out = 5): ## 有時候文本會有{}的內容 會出事..
    global client_gpt_4o
    if client_gpt_4o is None:
        print('Client has not been initialized. Call `initialize_client_gpt4o()` first.')
        raise ValueError("Client has not been initialized. Call `initialize_client_gpt4o()` first.")
    
    try:
        response =  await asyncio.wait_for(client_gpt_4o.chat.completions.create(
            model = intentDetect_,
            messages=conversation,
            response_format={ "type": "json_object" },
            temperature=0,
            # stop=['}']
        ), timeout=time_out)
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        print(f'If call_gpt execution time exceeds {time_out} seconds, call again')

        response = await client_gpt_4o.chat.completions.create(
            model = intentDetect_,
            messages=conversation,
            response_format={ "type": "json_object" },
            temperature=0,
            # stop=['}']
        )
        return response.choices[0].message.content
    except:
        time.sleep(0.5)
        response = await client_gpt_4o.chat.completions.create(
            model = intentDetect_,
            messages=conversation,
            response_format={ "type": "json_object" },
            temperature=0, 
        )
        return response.choices[0].message.content

async def close_client_gpt4o():
    global client_gpt_4o
    if client_gpt_4o is not None:
        await client_gpt_4o.close()
        client_gpt_4o = None


if __name__ == '__main__':
    async def run():
        initialize_client_gpt4o()
        try:
            conversation = [
                {'role': 'system', 'content': '請回復一個json格式的hello world'},
                {'role': 'user', 'content': ''}
            ]
            response = await call_gpt4o(conversation)
            print(response)
        finally:
            await close_client_gpt4o()

    asyncio.run(run())

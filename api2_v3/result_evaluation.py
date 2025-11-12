from openai import AsyncAzureOpenAI
import os
# import config


RESOURCE_ENDPOINT_ : str = os.getenv('MYAPP_GPT41MINI_RESOURCE_ENDPOINT')# type: ignore[assignment]
API_KEY_ = os.getenv('MYAPP_GPT41MINI_API_KEY')
intentDetect_ : str = os.getenv('MYAPP_GPT41MINI_INTENTDETECT')# type: ignore[assignment]
if RESOURCE_ENDPOINT_ is None or API_KEY_ is None or intentDetect_ is None:
    raise ValueError("Environment variables MYAPP_GPT41MINI_API_KEY, MYAPP_GPT41MINI_RESOURCE_ENDPOINT, and MYAPP_GPT41MINI_INTENTDETECT must be set.")

client = AsyncAzureOpenAI(
    azure_endpoint = RESOURCE_ENDPOINT_,
    api_key = API_KEY_,
    api_version = "2025-01-01-preview"
)


async def result_evaluation(answer):
    
    conversation =[
        {"role": "system", "content": f"You are a result check model. Here is the generated answer is: {answer}."},
        {"role": "user", "content": "If the answer uses numbered bullet points like '1.', '2.', '3.', etc., mark 'T'; if it uses any other format such as '-', or just text, mark 'F'. Only mark with the values 'T' or 'F'."}
    ]
        
    response = await client.chat.completions.create(
        model=intentDetect_,
        messages=conversation,
        n=1,
        stop=['}','User:'],
        temperature=0)
    generated_response = response.choices[0].message.content 
    # print(f'answer:{generated_response}')
    return generated_response


# result_evaluation 測試範例
if __name__ == '__main__':
    import asyncio
    answer = "My notebook's keyboard is not responding after resetting the PC: 1.aaa 2.bbb 3.ccc."
    asyncio.run(result_evaluation(answer))
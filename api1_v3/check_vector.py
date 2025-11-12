import aiohttp
import os
import time
from functools import wraps
import asyncio
# os.chdir("c:/Users/gina3_wang/OneDrive - ASUS/Folder/任務/20240103_email copilot/email_copilot")
# import config # 跑單一檔案測試時候要導入環境變數

client_http = None

def initialize_client_http():
    global client_http
    if client_http is None:
        client_http = aiohttp.ClientSession()

async def close_client_http():
    global client_http
    if client_http:
        await client_http.close()

def log_api_execution(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        response_content = None
        success = False
        error_message = None
        try:
            response = await func(*args, **kwargs)
            if response['status'] != 200:
                response = await func(*args, **kwargs)  # 第一次執行失敗 再跑一次
                if response['status'] != 200:
                    response_content = response.text
                    error_message = f"API returned error status {response['status']}: {response_content}"
                else:
                    success = True
                    response = response.json()
            else:
                success = True
                response = response.json()
        except aiohttp.ClientResponseError as e:
            response_content = response.text
            error_message = f"Received an invalid response with status code {e.status}. Response: {response_content}"
        except aiohttp.ClientConnectionError:
            error_message = "Unable to connect to the API. The API might be down or the URL is incorrect."
        except asyncio.TimeoutError:
            error_message = "The request timed out. The API might be slow or unresponsive."
        except Exception as e:
            error_message = f"Unexpected error: {e}"
        finally:
            end_time = time.time()
            log = {
                "start_time": int(start_time),
                "end_time": int(end_time),
                "duration": end_time - start_time,
                # 輸入的資料 寫入log
                "input_data": kwargs['data'] if 'data' in kwargs else None,
                "output_data": response if success else response_content,
                "error_message": error_message if not success else None,
                "success": success
            }
        return log
    return wrapper

redis_url_:str = os.getenv('MYAPP_VECTOR_API_URL') # type: ignore[assignment]
if redis_url_ is None:
    raise ValueError("Environment variable MYAPP_VECTOR_API_URL must be set.")

@log_api_execution
async def call_api(data):
    global client_http
    if client_http is None:
        raise ValueError("Client has not been initialized. Call `initialize_client_http()` first.")
    headers = {
        'accept': 'text/plain',
        'Content-Type': 'application/json'
    }
    url = redis_url_
    mock_return = {
    "status": 200,
    "message": "success(kr/us)",
    "result": {
        "faqs": [
        {
            "kb_no": 1042539,
            "websiteCode": "all",
            "productLine": "",
            "key": "genio_intent:4.0-all-1042539-999-70876",
            "type": "question",
            "hide": 999,
            "cosineSimilarity": 0.9601799249649
        }
        ],
        "record_found_at": 1
    }
    }
    return mock_return

def restructure_return(api_output):
    result = {}
    for i, item in enumerate(api_output, start=1):
        # 'Technical Support' if ans[0]['type'] == 'question' else ans[0]['type']
        result[f'intent_{i}'] = 'Technical Support' if item['type'] == 'question' else item['type']
        result[f'kb_no_{i}'] = item['kb_no']
        result[f'cosineSimilarity_{i}'] = item['cosineSimilarity']
        result[f'key_{i}'] = item['key']
    return result

async def call_redis_api(
        quest: str, 
        product_line: str, 
        website: str):
    '''
    pipeline to call api_intent and api_kb
    '''
    if website == 'gb':
        website = 'uk'
    question = quest
    data = [{
        "websiteCode": 'all',
        "keyword": question.lower(),
        "productLine": '',
        "version": "4.0",
        "n": 1,
        "hide_min": 0,
        "hide_max": 1999,
    }, {
        "websiteCode": website,
        "keyword": question.lower(),
        "productLine": product_line,
        "version": "4.0",
        "n": 4,
        "hide_min": 0,
        "hide_max": 999,
    }]
    response = await call_api(data=data)
    
    try:
        print("---call_redis_api response---", response)
        ans_intent = response['output_data']['result']['faqs']
        print("ans_intent:", ans_intent)
        ans_kb = response['output_data']['result']['faqs']
        print("ans_kb:", ans_kb)
        # 假設向量庫不足4筆 補上空值
        while len(ans_kb) < 4:
            default_item = {
                'kb_no': None,
                'websiteCode': None,
                'productLine': None,
                'key': None,
                'type': None,
                'hide': None,
                'cosineSimilarity': None
            }
            ans_kb.append(default_item) 
        print("ans_kb after append:", ans_kb)
        result_intent = restructure_return(ans_intent)
        print("result_intent:", result_intent)
        result_kb = restructure_return(ans_kb)
        print("result_kb:", result_kb)
    except Exception as e:
        response['success'] = False
        response['error_message'] = f'function api_intent error, error message: {e}'
        result_intent = {"error":"function call_redis_api error"}
        result_kb = {"error":"function call_redis_api error"}

    return response, result_intent, result_kb


if '__main__' == __name__:
    import time
    import asyncio
    a = time.time()
    quest = '''The Mediatek wi-fi 6 mt7921 wireless lan card of ASUS NUC BAREBONE disappears after a certain period of time after Windows starts'''
    product_line = 'nuc'
    website = 'latin'
    # result, ans = api_kb_request('''The wifi keeps disappearing, making it seem like the wifi card doesn't exist.''', 'notebook', 'ph')
    async def main():
        initialize_client_http()
        # api_result, data = await api_intent('''The Mediatek wi-fi 6 mt7921 wireless lan card of ASUS NUC BAREBONE disappears after a certain period of time after Windows starts''')
        api_result, intent_, kb_ = await call_redis_api(
            quest = quest, 
            product_line = product_line,
            website = website
        )
        print(api_result)
        print('-'*10)
        print(intent_)
        print('-'*10)
        print(kb_)
        print('-'*10)
        await close_client_http()
    
    a = time.time()
    asyncio.run(main())

    print(time.time() - a)
    



# def api_kb_request(quest, product_line, website):
#     import requests
#     if website == 'gb':
#         website = 'uk'
#     headers = {
#         'accept': 'text/plain',
#         'apikey': 'moneyislife',
#         'Content-Type': 'application/json'
#     }
#     url = 'https://chatfetch.azurewebsites.net/api/v1/faqSearch'
#     question = '''Mediatek wi-fi 6 mt7921 wireless lan card disappears after a certain time after Windows startup, and does not appear in the adapter or device manager. Even after following the instructions to reset the BIOS to default settings and uninstall/reinstall the card, the issue persists. Please provide a fundamental solution without the need for complicated operations or losing all previous information.'''
#     data = {
#         "websiteCode": 'latin',
#         "keyword": question.lower(),
#         "version": "4.0",
#         "n": 4,
#         "hide_min": 0,
#         "hide_max": 1999,
#         "productLine":'nuc'
#     }
#     response = requests.post(url, headers=headers, json=data)
#     ans = response.json()['result']['faqs']
    
#     result = {}
#     for i, item in enumerate(ans, start=1):
#         result[f'kb_no_{i}'] = item['kb_no']
#         result[f'cosineSimilarity_{i}'] = item['cosineSimilarity']
#     return result, ans
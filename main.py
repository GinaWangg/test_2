# -*- coding: utf-8 -*-
import config
##### Application Insights (Azure Monitor) #####
from azure.identity import DefaultAzureCredential
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
import os

sub_id:str = os.getenv("MYAPP_AZURE_SUBSCRIPTION_ID") # type: ignore[assignment]
client = ApplicationInsightsManagementClient(credential=DefaultAzureCredential(), subscription_id=sub_id)
################################################

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse  # 拿來return json
from pydantic import BaseModel, ConfigDict
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
from typing import Optional, Any, List
import time
import random


env = os.getenv("MYAPP_ENVIRONMENT")
if env is None :
    raise ValueError("Environment variable MYAPP_ENVIRONMENT is not set.")
if env == '-prod':
    config_doc = None
else:
    config_doc = "/docs"

app = FastAPI(docs_url=config_doc, redoc_url=None)
app.mount("/static", StaticFiles(directory="./"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers='Content-Type',
    max_age = 3600
)

#### 定義錯誤訊息 ####
class CustomHTTPException(HTTPException):
    def __init__(self, status_code: float, detail: str, output: dict = None):
        super().__init__(status_code=status_code, detail=detail)
        self.detail = {"status": status_code, "message": detail, "output": output}

@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException, output: dict = None):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

####### input data validation #######
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import json
    start_time = time.time()
    _id = f'RequestValidationError-{start_time}-{env}'
    return_content = {
        "status": 400,
        "message": "(Validation Error)Unprocessable Entity",
        "output": None
    }
    partition_key = request.url.path if request.url.path.count("/") == 2 else "/v1" + request.url.path

    raw_body = await request.body()
    user_input = {}
    try:
        user_input = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        user_input = {"raw_body": raw_body.decode("utf-8")}

    errorr_message = f'(Validation Error): {exc.errors()}, User Input: {user_input}'
    
    return JSONResponse(status_code=400, content=return_content)

#### 第一支api ####
class Api1(BaseModel):
    case_id: Any
    email: Any
    phone: Any
    case_date: Any
    site: Any
    product_type: Any
    email_content: Any
    product_model: Optional[str] = ''
    product_sn: Optional[str] = None
    problem_description_content: Optional[str] = None
from api1_v3.email_detect_main import email_detect as email_detect_v3

@app.post("/v3/emailDetect")
async def api_1_v3(input: Api1):
    partition_key = "/v3/emailDetect"  # Partition Key 設置為 API 路徑     
    start_time = time.time()
    try:
        case_id = input.case_id
        _id = f'{case_id}-{int(start_time)}{env}'
        email = input.email
        phone = input.phone
        case_date = input.case_date
        site = input.site.lower()
        product_type = input.product_type
        email_content = input.email_content
        product_model = input.product_model
        product_sn = input.product_sn
        problem_description_content = input.problem_description_content
        data_type_mappings = {
            'case_id': str,
            'email': str,
            'phone': str,
            'case_date': int,
            'site': str,
            'product_type': str,
            'email_content': str
        }
        output = None
        for field, expected_type in data_type_mappings.items():
            value = locals()[field]
            if (not isinstance(value, expected_type)) | (value == None) | (value == '') :
                output = {
                    "status": 400,
                    "message": f"(Validation Error)The {field}({value}) field has an incorrect format. Please recheck the input data.",
                    "output": None
                }
                break
        if output is None:
            output = await email_detect_v3(_id, case_id,email,
                    phone,case_date,site,
                    product_type,
                    email_content,
                    product_model,
                    product_sn,
                    problem_description_content)
            output['status']
            output['message']
            output['output']
        message_detail = None
    except Exception as e:
        import traceback
        message_detail = traceback.format_exc()
        print(e)
        output = {
            "status": 500,
            "message": "Internal Server Error",
            "output": None
        }
    finally:
        if output is None:
            output = {
                "status": 500,
                "message": "Unknown Error",
                "output": None
            }
        if output['status'] != 200:
            raise CustomHTTPException(status_code=output['status'], detail=output['message'], output=output['output'])
        else:
            return output


#### 第二支api ####
#### Author: Vickie Chu
#### Modify Date: 2025-08-06
#### Version: v3

class Api2_v3(BaseModel):
    case_id: Any
    product_type: Any
    split_question: Any
    rag_recall_reason: Optional[Any] = None
    kb_no: Any


@app.post("/v3/kbRAG") 
async def api_2_v3(input: Api2_v3):
    partition_key = "/v3/kbRAG"  # Partition Key 設置為 API 路徑
    start_time = time.time()
    try: 
        current_dir = os.path.abspath(os.path.dirname(__file__))
        sys.path.append(os.path.join(current_dir, 'api2_v3'))
        from api2_v3.kb_rag_main import kb_rag as kb_rag_v3
        case_id = input.case_id
        _id = f'{case_id}-{int(start_time)}{env}'
        product_type = input.product_type
        split_question = input.split_question
        rag_recall_reason = input.rag_recall_reason
        kb_no = input.kb_no
        data_type_mappings = {
            'case_id': str,
            'product_type': str,
            'split_question': str,
            'rag_recall_reason': str,
            'kb_no': int
        }
        output = None
        for field, expected_type in data_type_mappings.items():
            value = locals()[field]
            if (not isinstance(value, expected_type)):
                output = {
                    "status": 400,
                    "message": f"(Validation Error)The {field}({value}) field has an incorrect format. Please recheck the input data.",
                    "output": None
                }
                break
            if field in ['case_id', 'product_type', 'split_question', 'kb_no']:
                if (value == '') | (value == None):
                    output = {
                        "status": 400,
                        "message": f"(Validation Error)The {field}({value}) field has an incorrect format. Please recheck the input data.",
                        "output": None
                    }
                    break
        if output is None:
            output = await kb_rag_v3(_id, case_id,
                    product_type,                 
                    split_question,                 
                    rag_recall_reason,
                    kb_no,
                    Site_lang_mappings, 
                    KB_mappings
                    )
            output['status']
            output['message']
            output['output']
        message_detail = None
    except Exception as e:
        import traceback
        message_detail = traceback.format_exc()
        print(e)
        output = {
            "status": 500,
            "message": "Internal Server Error",
            "output": None
        }
    finally:
        if output['status'] != 200:
            raise CustomHTTPException(status_code=output['status'], detail=output['message'], output=output['output'])
        else:
            return output


#### 第三支api ####
#### Author: Vickie Chu
#### Modify Date: 2024-12-12
#### Version: v3

class AgentResponseInfo(BaseModel):
    extract_type: Any
    extract_type_num: Any
    gpt_output: Any
    intent: Any
    agent_response_kb: Optional[Any] = None

class Api3_v3(BaseModel):
    case_id: Any
    agent_response_date: Any
    agent_response_info: List[AgentResponseInfo]
        
@app.post("/v3/emailFeedback")
async def api_3_v3(input: Api3_v3):
    partition_key = "/v3/emailFeedback"  # Partition Key 設置為 API 路徑  
    start_time = time.time()
    try:
        from api3_v3.datatype_validation import api3_v3_validation
        case_id = input.case_id
        _id = f'{case_id}-{int(start_time)}{env}'
        agent_response_date = input.agent_response_date           
        agent_response_info_dicts = [info.model_dump() for info in input.agent_response_info] # 將 agent_response_info 中的每個項目轉換為字典
        output = api3_v3_validation(case_id, agent_response_date, agent_response_info_dicts)
        if output is None:
            from api3_v3.email_feedback_main_v3 import email_feedback
            output = await email_feedback(_id, case_id,
                    agent_response_date,
                    agent_response_info_dicts)
            output['status']
            output['message']
            output['output']
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)
        output = {
            "status": 500,
            "message": "Internal Server Error",
            "output": None
        }
    finally:
        if output['status'] != 200:
            raise CustomHTTPException(status_code=output['status'], detail=output['message'], output=output['output'])
        else:
            return output

@app.get('/')
def read_root():
    return {"status": "ok"}


#### 讀定義表 ####
@app.get('/update_KB')
def update_KB():
    global KB_mappings
    try:
        import json
        with open('../kb_mappings.json', 'r', encoding='utf-8') as f:
            KB_mappings = json.load(f)
    except:
        print('start update KB_mappings from cosmosDB')
        from azure.cosmos import CosmosClient
        client = CosmosClient(
                url = url_,
                credential = key_,
                consistency_level='Session' 
                )
        
        database_name = database_name_r_
        container_name = "ApChatbotKnowledge"
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        query = """SELECT * FROM c"""
        results = container.query_items(query, enable_cross_partition_query=True)
        new_KB_mappings = {
            f"{item.get('kb_no')}_{item.get('lang')}": {
                'title': item.get('title'),
                'summary': item.get('summary'),
                'content': item.get('content')[:10000]
                } for item in results
            }

        KB_mappings = new_KB_mappings
    print('KB_mappings update success')
    return "KB_mappings update success" 

@app.get('/update_site_lang')
def update_site_lang():

    from azure.cosmos import CosmosClient

    global Site_lang_mappings

    client = CosmosClient(
            url = url_,
            credential = key_,
            consistency_level='Session' 
            )

    database_name = database_name_r_
    container_name = "FAQ_LanguageMapping_ForOpenAI"
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    query = """SELECT * FROM c"""
    results = container.query_items(query, enable_cross_partition_query=True)
    Site_lang = {
        f"{item.get('websitecode')}": {
            'lang': item.get('lang')
            } for item in results
        }

    Site_lang_mappings = Site_lang
    print('Site_lang_mappings update success')
    return "Site_lang_mappings update success" 

@app.on_event("startup")
async def read_cosmos():
    # update_KB()
    # update_site_lang()
    current_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(os.path.join(current_dir, 'api1'))
    from api1_v3.get_translate import initialize_google_translate as initialize_google_translate_v3
    initialize_google_translate_v3()


#### 定期重讀定義表 ####
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone

scheduler = BackgroundScheduler(timezone=timezone('Asia/Taipei'))

# 設置不同的任務和執行間隔
scheduler.add_job(update_KB, IntervalTrigger(hours=1, timezone=timezone('Asia/Taipei')))
scheduler.add_job(update_site_lang, IntervalTrigger(hours=1, timezone=timezone('Asia/Taipei')))
scheduler.start()



# 本機測試要這個
if __name__ == "__main__":
    import uvicorn  
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    # post 要看成效 http://127.0.0.1:8000/docs
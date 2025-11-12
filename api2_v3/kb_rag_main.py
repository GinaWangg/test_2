##### Application Insights (Azure Monitor) #####
from azure.identity import DefaultAzureCredential
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
import os
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.requests import trace
from opencensus.trace import config_integration
# import config

# # 手動加入路徑
# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

sub_id:str = os.getenv("MYAPP_AZURE_SUBSCRIPTION_ID") # type: ignore[assignment]
client = ApplicationInsightsManagementClient(credential=DefaultAzureCredential(), subscription_id=sub_id)

# 2. 啟用 API 的 Application Insights 追蹤功能
# instrumentation_key = os.getenv("APPLICATION_INSIGHTS_INSTRUMENTATION_KEY")
# instrumentation_key = config_rag['azure_monitor']['instrumentationKey']
instrumentation_key = '76c9ee44-4919-47f7-b85c-5b0b704865bf'
# Set up logging to Azure Application Insights
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(AzureLogHandler(connection_string=f'InstrumentationKey={instrumentation_key}'))

# Set up tracing to Azure Application Insights
tracer = Tracer(exporter=AzureExporter(connection_string=f'InstrumentationKey={instrumentation_key}'),
                sampler=ProbabilitySampler(1.0))

# Enable requests tracing
config_integration.trace_integrations(['requests'])
################################################

import time
from tqdm import tqdm
import json
import pandas as pd
import numpy as np
import sys
pd.set_option('display.max_colwidth', None)  # 設置無限制列寬
pd.set_option('display.max_rows', None)      # 設置無限制顯示行數
# from ragas.metrics import (
#     answer_relevancy,
#     faithfulness,
#     context_recall,
#     context_precision,
#     context_relevancy
# )
from azure.cosmos import CosmosClient
import asyncio
import nest_asyncio
nest_asyncio.apply()
import traceback # for error handling

# current_dir = os.path.abspath(os.path.dirname(__file__))
# sys.path.append(os.path.join(current_dir, 'api2'))
# print(current_dir)
# import os
# print(os.getcwd())

import api2_v3.search_cosmos as get_kb_info
import api2_v3.reply_with_faq as get_rag
import api2_v3.result_evaluation as get_rag_evaluation
import api2_v3.append_url_with_newline as get_kb_title
import api2_v3.write_cosmos_rag as insert_cosmosDB


search_cosmos_caseid_info = get_kb_info.search_cosmos_caseid_info
reply_with_faq = get_rag.reply_with_faq
summarize_question = get_rag.summarize_question
translate_text = get_rag.translate_text
result_evaluation = get_rag_evaluation.result_evaluation
append_url_with_newline = get_kb_title.append_url_with_newline
remove_contact_sentence = get_kb_title.remove_contact_sentence
append_url_with_newline_global = get_kb_title.append_url_with_newline_global
write_cosmosDB_rag = insert_cosmosDB.write_cosmosDB_rag


# # Function to be monitored
# def monitored_reply_with_faq(question, kb_no, lang):
#     with tracer.span(name="reply_with_faq"):
#         result = reply_with_faq(question, kb_no, lang)
#         return result


# 執行RAG
async def rag_test_dev(question, kb_no, email_lang, content, product_type):
    # content = rag_info['content'].iloc[0]
    # lang = lang
    # email_lang = email_lang
    
    try:
        gpt_output = await reply_with_faq(content, question, email_lang, product_type)

    except:
        await asyncio.sleep(3)
        gpt_output = await reply_with_faq(content, question, email_lang, product_type)

    eva = await result_evaluation(answer = gpt_output)
    if eva == 'T':
        return gpt_output
    else:
        # 再次嘗試
        try:
            gpt_output = await reply_with_faq(content, question, email_lang, product_type)
        except:
            await asyncio.sleep(3)
            gpt_output = await reply_with_faq(content, question, email_lang, product_type)
        
        eva = await result_evaluation(answer = gpt_output)
        if eva == 'T':
            return gpt_output
        else:
            return 'miss'


# # 定義輸入數據 (待串接 cosmos DB 後調整)
# case_id = 'N24080002768-0001'
# rag_recall_reason = ''
# kb_no = 1050047

# # 匯入 Global variable
# import pickle
# kb_mappings_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_draft\kb_mappings.pkl'
# site_lang_mappings_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_draft\Site_lang_mappings.pkl'
# with open(kb_mappings_path, 'rb') as file:
#     KB_mappings = pickle.load(file)

# with open(site_lang_mappings_path, 'rb') as file:
#     Site_lang_mappings = pickle.load(file)

# # # 其他範例
# # case_id = 'A24080007314-0001'
# # rag_recall_reason = ''
# # kb_no = 1014276 



async def kb_rag_pre(case_id, product_type, split_question, rag_recall_reason, kb_no, KB_mappings, Site_lang_mappings):
    start_time  = int(time.time())
    
    time_1 = time.perf_counter()
    # 執行查詢 CosmosDB 取得 case_id 數據記錄
    rag_info = search_cosmos_caseid_info(case_id)
    
    # 整理資料
    if rag_info is None:
        rag_info = {}
    rag_info['product_type'] = product_type
    rag_info['split_question'] = split_question
    rag_info['rag_recall_reason'] = rag_recall_reason
    rag_info['kb_no'] = kb_no
    rag_info['email_lang'] = rag_info['email_lang'].str.lower()

    time_2 = time.perf_counter()
    execution_time = time_2 - time_1
    print(f"導入 case id 相關數據 (取得 API1 數據): {execution_time:.4f} 秒")
    
    
    time_1 = time.perf_counter()
    ### 新版取得 lang 的方式 7/5
    rag_info['lang'] = [''] * len(rag_info['site'])  # 預先初始化列表
    for idx, site in tqdm(enumerate(rag_info['site'])):
        try:
            if site == 'gb':
                site = 'uk'
            lang = Site_lang_mappings.get(site, {}).get('lang')
            if lang is None:
                raise ValueError(f"Unable to retrieve language for site {site}")
            rag_info.loc[idx, 'lang'] = lang
        except Exception as e:
            raise Exception(f"Error at index {idx}: {e}")
    
    # 建立 site_replaced 欄位
    def find_site_replaced(email_lang):
        if email_lang == 'zh-hant':
            lang_to_find = 'zh-hk'
        else:
            lang_to_find = email_lang
        preferred_country_code_suffix = lang_to_find[-2:]
       
        # 找所有對應語系的 country code
        country_codes = [key for key, value in Site_lang_mappings.items() if value['lang'] == lang_to_find]

        # 正常情況有 country_codes 就照原本方式選
        if country_codes:
            selected_country_code = next((code for code in country_codes if code.endswith(preferred_country_code_suffix)), country_codes[0])
            print(f"country_codes: {country_codes}, selected_country_code: {selected_country_code}")
            return selected_country_code[-2:]

        # 沒有對應語系，優先選用 preferred_country_code_suffix
        if preferred_country_code_suffix:
            selected_country_code = preferred_country_code_suffix
        else:
            selected_country_code = 'us'
        return selected_country_code


    # 應用 find_site_replaced 函數到 rag_info 的每一行
    rag_info['site_replaced'] = rag_info['email_lang'].apply(find_site_replaced)  


    # 確認 case id 的 top1 kb 是否有 email lang 的 kb 資訊
    def check_kb_no_in_emaillang(kb_no, email_lang):
        key_to_search = f"{kb_no}_{email_lang}"
        return 'T' if key_to_search in KB_mappings else 'F'
    rag_info['kb_no_emaillang'] = rag_info.apply(lambda row: check_kb_no_in_emaillang(row['kb_no'], row['email_lang']), axis=1)

    ### 新版取得 kb title, summary, content 的方式 7/5
    # 預先初始化 rag_info 的新欄位
    for field in ['title', 'summary', 'content']:
        rag_info[field] = [''] * len(rag_info['kb_no'])

    for idx, (kb_no, email_lang, lang, site) in tqdm(enumerate(zip(rag_info['kb_no'], rag_info['email_lang'], rag_info['lang'], rag_info['site'])), total=len(rag_info['kb_no'])):
        try:
            # 創建查詢 ID，首先使用 kb_no 和網站站台的語系
            query_id_lang = f"{kb_no}_{lang}"

            # 檢查網站站台支援的語系是否存在於 KB_mappings 中
            if query_id_lang not in KB_mappings:
                raise ValueError(f"No information found for kb_no {kb_no} and lang {lang} on site {site}")

            # 創建查詢 ID，首先使用 kb_no 和 email_lang
            query_id_email_lang = f"{kb_no}_{email_lang}"

            # 特殊處理當 email_lang 是 zh-cn 的情況，將其轉換為 en-us
            if email_lang == 'zh-cn':
                query_id_email_lang = f"{kb_no}_en-us"

            # 嘗試從 KB_mappings 中獲取 {kb_no}_{email_lang} 的資訊
            kb_info_email_lang = KB_mappings.get(query_id_email_lang)

            # 如果 {kb_no}_{email_lang} 沒有資訊，則回退到 {kb_no}_en-us
            kb_info_global = KB_mappings.get(f"{kb_no}_en-us")

            # 如果 {kb_no}_en-us 沒有資訊，則回退到 {kb_no}_{lang} (site語系)
            kb_info_site_lang = KB_mappings.get(query_id_lang)

            # 更新 rag_info 中的相應字段，優先使用 email_lang，如果沒有則使用 en-us，最後使用 site 語系
            for field in ['title', 'summary', 'content']:
                if kb_info_email_lang and field in kb_info_email_lang:
                    rag_info.loc[idx, field] = kb_info_email_lang[field]
                elif kb_info_global and field in kb_info_global:
                    rag_info.loc[idx, field] = kb_info_global[field]
                elif kb_info_site_lang and field in kb_info_site_lang:
                    rag_info.loc[idx, field] = kb_info_site_lang[field] 
                    # 修改 site_replaced 欄位,改成 site 語系
                    rag_info['site_replaced'] = rag_info['lang'].apply(find_site_replaced)
                else:
                    raise ValueError(f"Field '{field}' not found for {query_id_email_lang} or {query_id_lang}")
        except Exception as e:
            raise ValueError(f"Error for kb_no {kb_no} and email_lang {email_lang}: {str(e)}")

    # 如果 rag_info 不是 DataFrame，將其轉換為 DataFrame
    if not isinstance(rag_info, pd.DataFrame):
        rag_info = pd.DataFrame(rag_info)

    time_2 = time.perf_counter()
    execution_time = time_2 - time_1
    print(f"導入 KB 相關數據 (查找 Cosmos): {execution_time:.4f} 秒")


    time_1 = time.perf_counter()
    async def process_rag_draft(idx, email_content, kb_no, email_lang, rag_info):
        try:
            kb_no = kb_no.split(',')[0] if isinstance(kb_no, str) else kb_no
            content = rag_info['content'].iloc[0]
            rag_result = await rag_test_dev(email_content, kb_no, email_lang, content, product_type)
            # print(f'rag_result: {rag_result}')
            if rag_result is None or rag_result == '':
                raise ValueError(f"RAG returned empty result for kb_no {kb_no} and lang {email_lang}")
            
            return idx, rag_result
        except Exception as e:
            raise ValueError(f"Error at index {idx} for kb_no {kb_no} and lang {email_lang}: {str(e)}")
        

    async def process_first_sentence(idx, question, summary, email_lang, product_type):
        try:
            return idx, await summarize_question(question, summary, email_lang, product_type)
        except:
            print('wrong: ', idx)
            return idx, ''

    async def process_close_sentence(idx, email_lang):
        try:
            return idx, await translate_text(email_lang)
        except:
            print('wrong: ', idx)
            return idx, ''

    

    # 創建所有任務
    rag_draft_tasks = [
        process_rag_draft(idx, split_question, kb_no, email_lang, rag_info)
        for idx, (split_question, kb_no, email_lang) in enumerate(zip(rag_info['split_question'], rag_info['kb_no'], rag_info['email_lang']))
        if print(f"email_lang: {email_lang}") or True
    ]
    
    first_sentence_tasks = [
        process_first_sentence(idx, question, summary, email_lang, product_type)
        for idx, (question, summary, email_lang, product_type) in enumerate(zip(rag_info['split_question'], rag_info['summary'], rag_info['email_lang'], rag_info['product_type']))
        if print(f"process_first_sentence lang: {email_lang}") or True
    ]
    
    close_sentence_tasks = [
        process_close_sentence(idx, email_lang)
        for idx, lang in enumerate(rag_info['email_lang'])
        if print(f"process_close_sentence lang: {email_lang}") or True
    ]
    
    # 同時執行所有任務
    all_results = await asyncio.gather(
        asyncio.gather(*rag_draft_tasks),
        asyncio.gather(*first_sentence_tasks),
        asyncio.gather(*close_sentence_tasks)
    )
    
    # 解包結果
    rag_draft_results, first_sentence_results, close_sentence_results = all_results
    
    # 將結果存入 rag_info
    rag_info['rag_draft'] = dict(rag_draft_results)
    rag_info['first_sentence'] = dict(first_sentence_results)
    rag_info['close_sentence'] = dict(close_sentence_results)
    
    # 確保 rag_info 是一個 DataFrame
    if not isinstance(rag_info, pd.DataFrame):
        rag_info = pd.DataFrame(rag_info)
    

    # 新增kb URL至RAG
    rag_info['rag_draft'] = rag_info['rag_draft'].apply(remove_contact_sentence)
    
    # kb url 取用順序: (1) User 語系的 KB URL (2) Global KB URL (3) Site 語系的 KB URL
    rag_info['rag'] = rag_info.apply(
    lambda row: append_url_with_newline_global(row) 
    if (row['site_replaced'] == 'us') or (row['site_replaced'] == 'cn')
    else append_url_with_newline(row),
    # if row['kb_no_emaillang'] == 'T' 
    # else append_url_with_newline_global(row), 
    axis=1
    )

    
    time_2 = time.perf_counter()
    execution_time = time_2 - time_1
    print(f"生成 RAG 內容: {execution_time:.4f} 秒")



    rag_output_final = rag_info

    end_time  = int(time.time())

    if len(rag_output_final) ==1:
        output =  {
        "case_id": rag_output_final['case_id'][0],
        "gpt_extract": {
            "rag": rag_output_final['rag'][0],
            "lang": rag_output_final['email_lang'][0]
        },
        "check_info": {
            "answer_relevancy": 0,
            "start_time_ts": start_time,
            "end_time_ts": end_time,
            "lang": rag_output_final['email_lang'][0]
        }}
    
    else:
        output = None
    return output



async def kb_rag(_id, case_id, product_type,split_question, rag_recall_reason, kb_no, Site_lang_mappings, KB_mappings):
    input_data = {
        "case_id": case_id,
        "product_type": product_type,
        "split_question": split_question,
        "rag_recall_reason": rag_recall_reason,
        "kb_no": kb_no
    }
    try:
        output = await kb_rag_pre(
            case_id = case_id, 
            product_type = product_type,
            split_question = split_question,
            rag_recall_reason = rag_recall_reason, 
            kb_no = kb_no,
            Site_lang_mappings = Site_lang_mappings,
            KB_mappings = KB_mappings)
        error = None
        error_detail = None
        status = 200
        return_output = {
            "status": status,
            "message": "Success",
            "output": output
        }

    except ValueError as e:
        status = 400
        output = None
        error = {"error": str(e)}
        tb = traceback.format_exc()
        error_detail = {"traceback": tb}
        print(f'-------- (api2) case_id:{case_id}--------')
        print(error) 
        return_output = {
            "status": status,
            "message": e.args[0], 
            "output": output
        }
    except Exception as e:
        status = 400
        output = None
        error = 'ERROR'
        tb = traceback.format_exc()
        error_detail =  {"error": str(e), "traceback": tb}
        print(f'-------- (api2) case_id:{case_id}--------')
        print(error_detail)
        return_output = {
            "status": status,
            "message": error, 
            "output": output
        }
    finally:
        write_cosmosDB_rag(
            _id,
            case_id, 
            input_data = input_data, 
            output_data = output, 
            error = error,
            error_detail = error_detail)    

    return return_output

# 單題測試
if __name__ == '__main__':
    import asyncio

    # _id = 'test'
    # case_id = 'E25060021275-0001'
    # split_question = 'Telefonen laddar långsamt och blir väldigt varm trots att laddningsinställningen är aktiv.'
    # rag_recall_reason=''
    # kb_no = 1011555

    # _id = 'test'
    # case_id = 'E25030060853-0002'
    # split_question = 'My notebook has recurring startup difficulties. There seems to be a problem turning it on, possibly a loose connection at the power button. Additionally, the keyboard was already replaced in 2021 and 2023.'
    # rag_recall_reason=''
    # kb_no = 1014276

    # _id = 'test'
    # case_id = 'A2502011857-0009'
    # split_question = '我的筆記本又出現藍底白字的畫面，通常是在打開銀行網頁時。'
    # rag_recall_reason=''
    # kb_no = 1042499

    _id = 'test'
    case_id = 'E25060022532-0001'
    product_type = 'notebook'
    split_question = 'Min Notebook-skærm er løftet i bunden, og der stikker et kabel ud.'
    rag_recall_reason=''
    kb_no = 1015072

    import pickle
    kb_mappings_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_draft\kb_mappings.pkl'
    site_lang_mappings_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_draft\Site_lang_mappings.pkl'
    with open(kb_mappings_path, 'rb') as file:
        KB_mappings = pickle.load(file)

    with open(site_lang_mappings_path, 'rb') as file:
        Site_lang_mappings = pickle.load(file)
    print(asyncio.run(kb_rag(_id, case_id, product_type, split_question, rag_recall_reason, kb_no, Site_lang_mappings, KB_mappings)))

# # 多題測試 (測試失敗)
# import asyncio
# import pickle
# import pandas as pd

# def load_testing_set(file_path):
#     """ 讀取 Excel 檔案，回傳 DataFrame """
#     try:
#         testing_set = pd.read_excel(file_path)
#         if testing_set.empty:
#             raise ValueError("測試資料 testing_set 為空，請確認 Excel 檔案內容")
#         return testing_set
#     except Exception as e:
#         raise ValueError(f"讀取 Excel 檔案失敗: {e}")

# def load_pickle_file(file_path):
#     """ 讀取 pickle 檔案 """
#     try:
#         with open(file_path, 'rb') as file:
#             return pickle.load(file)
#     except Exception as e:
#         raise ValueError(f"讀取 {file_path} 失敗: {e}")

# if __name__ == '__main__':
#     # 設定檔案路徑
#     file_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_dev\dev\api2\testing_caseid_20250218.xlsx'
#     kb_mappings_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_draft\kb_mappings.pkl'
#     site_lang_mappings_path = r'D:\Python_project\2024Q1_email_copilot\email_copilot_draft\Site_lang_mappings.pkl'

#     # 讀取測試資料
#     testing_set = load_testing_set(file_path)

#     # 取得第一筆測試數據
#     first_row = testing_set.iloc[0]

#     # 從 testing_set 取得對應欄位值
#     _id = first_row['_id']
#     case_id = first_row['case_id']
#     kb_no = first_row['kb_no']
#     split_question = first_row['split_question']
#     rag_recall_reason = first_row['rag_recall_reason']

#     # 載入 pickle 檔案
#     KB_mappings = load_pickle_file(kb_mappings_path)
#     Site_lang_mappings = load_pickle_file(site_lang_mappings_path)

#     # 執行 asyncio 任務
#     print(asyncio.run(kb_rag(_id, case_id, split_question, rag_recall_reason, kb_no, Site_lang_mappings, KB_mappings)))



# # Manual insert Global variable
# # 1
# import configparser
# from azure.cosmos import CosmosClient
# import pickle
# ini_filename = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)), 'config_main.ini')
# # ini_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_rag.ini')
# # ini_filename = 'D:\\Python_project\\2024Q1_email_copilot\\email_copilot_draft\\email_copilot_dev_latest\\dev\\api2\\config_rag.ini'
# config = configparser.ConfigParser()
# config.read(ini_filename)

# # global KB_mappings

# client = CosmosClient(
#         url = config['cosmosdev']['url'],
#         credential = config['cosmosdev']['key'],
#         consistency_level='Session' 
#         )

# database_name = config['cosmosdev']['database_name_r']
# container_name = "ApChatbotKnowledge"
# database = client.get_database_client(database_name)
# container = database.get_container_client(container_name)

# query = """SELECT * FROM c"""
# results = container.query_items(query, enable_cross_partition_query=True)
# new_KB_mappings = {
#     f"{item.get('kb_no')}_{item.get('lang')}": {
#         'title': item.get('title'),
#         'summary': item.get('summary'),
#         'content': item.get('content')[:10000]
#         } for item in results
#     }

# KB_mappings = new_KB_mappings

# with open('kb_mappings.pkl', 'wb') as file:
#     pickle.dump(KB_mappings, file)
# print('KB_mappings update success and saved to KB_mappings.pkl')


# # 2
# import configparser
# from azure.cosmos import CosmosClient
# import pickle

# ini_filename = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)), 'config_main.ini')
# config = configparser.ConfigParser()
# config.read(ini_filename)

# global Site_lang_mappings

# client = CosmosClient(
#         url = config['cosmosdev']['url'],
#         credential = config['cosmosdev']['key'],
#         consistency_level='Session' 
#         )

# database_name = config['cosmosdev']['database_name_r']
# container_name = "FAQ_LanguageMapping_ForOpenAI"
# database = client.get_database_client(database_name)
# container = database.get_container_client(container_name)

# query = """SELECT * FROM c"""
# results = container.query_items(query, enable_cross_partition_query=True)
# Site_lang = {
#     f"{item.get('websitecode')}": {
#         'lang': item.get('lang')
#         } for item in results
#     }

# Site_lang_mappings = Site_lang
# with open('Site_lang_mappings.pkl', 'wb') as file:
#     pickle.dump(Site_lang_mappings, file)
# print('Site_lang_mappings update success')
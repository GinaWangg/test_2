from azure.cosmos import CosmosClient
import time
import os
import pandas as pd
pd.set_option('display.max_colwidth', None)  # 設置無限制列寬
pd.set_option('display.max_rows', None)      # 設置無限制顯示行數


# # 1. 查詢 Site 所屬語言
# def search_cosmos_site_lang(site):
#     # ini_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_rag.ini')
#     ini_filename = 'D:\\Python_project\\2024Q1_email_copilot\\email_copilot_draft\\email_copilot_dev\\dev\\api2\\config_rag.ini'
#     config_rag = configparser.ConfigParser()
#     config_rag.read(ini_filename)

#     # 建立 CosmosClient
#     client = CosmosClient(
#         url = config_rag['cosmosdev']['url'],
#         credential = config_rag['cosmosdev']['key'],
#         consistency_level='Session'
#         )
    
#     # 取得 database 和 container
#     database_name = "ml-dev"
#     container_name = "FAQ_LanguageMapping_ForOpenAI"# 類似 from [database_name].[dbo].[container_name]
#     database = client.get_database_client(database_name)
#     container = database.get_container_client(container_name)
    
#     # 定義查詢語句
#     query = f"select c.lang from c where c.websitecode = '{site}'"
    
#     # 執行查詢
#     results = container.query_items(query, enable_cross_partition_query=True)

#     # 將查詢結果轉換為 DataFrame
#     items = [item for item in results]
#     kb_lang = pd.DataFrame(items)
    
#     return kb_lang

# # 2. 查詢 kb_no 資料庫資訊
# def search_cosmos_kb_info(kb_no, lang):
#     # ini_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_rag.ini')
#     ini_filename = 'D:\\Python_project\\2024Q1_email_copilot\\email_copilot_draft\\email_copilot_dev\\dev\\api2\\config_rag.ini'
#     config_rag = configparser.ConfigParser()
#     config_rag.read(ini_filename)

#     client = CosmosClient(
#         url = config_rag['cosmosdev']['url'],
#         credential = config_rag['cosmosdev']['key'],
#         consistency_level='Session'
#         )
    
#     database_name = "ml-dev"
#     container_name = "ApChatbotKnowledge"# 類似 from [database_name].[dbo].[container_name]
#     database = client.get_database_client(database_name)
#     container = database.get_container_client(container_name)
    
#     query = f'''select c.kb_no, c.lang, c.title, c.content, c.summary 
#             from c 
#             where c.kb_no = {kb_no} and c.lang = '{lang}' '''

#     results = container.query_items(query, enable_cross_partition_query=True)
    
#     items = [item for item in results]
#     kb_info = pd.DataFrame(items)
    
#     return kb_info

# 3. 查詢 API1 存取的 Case_id 資訊
def search_cosmos_caseid_info(case_id):
    url_ = os.getenv("MYAPP_COSMOS_URL")
    key_ = os.getenv("MYAPP_COSMOS_KEY")
    database_name_ = os.getenv("MYAPP_COSMOS_WRITE_DATABASE_NAME")
    if not url_ or not key_ or not database_name_:
        raise ValueError("Cosmos DB connection details are not set in environment variables.")

    
    # 建立 CosmosClient
    client = CosmosClient(
        url = url_,
        credential = key_,
        consistency_level='Session'
        )
    
    # 取得 database 和 container
    # database_name = "email_copilot"
    database_name = database_name_
    container_name = 'emailDetect'
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)
    
    # 定義查詢語句
    query = f'''
    select c.case_id, c.api_version, c.input_data.site, c.input_data.product_type, c.input_data.email_content, 
           c.output_data.gpt_extract.user_summary, c.output_data.check_info.lang as email_lang, c.output_data.gpt_extract.type as type
    from c 
    where c.case_id = '{case_id}' 
    order by c.id desc 
    offset 0 
    limit 1
    '''
    
    # 執行查詢
    results = container.query_items(query, enable_cross_partition_query=True)
    
    # 將查詢結果轉換為 DataFrame
    items = [item for item in results]
    rag_info = pd.DataFrame(items)

    # 檢查結果是否為空
    if rag_info.empty:
        raise ValueError(f'Case id: {case_id} not found. Please confirm (1) if the case_id is entered correctly (2) execute EmailDetect API before generating the RAG.')
    
    # 檢查是否有 'type' 欄位，且 type 是否為 'unclear_description'
    if 'type' in rag_info.columns and 'unclear_description' in rag_info['type'].values:
        raise ValueError(f'Case id: {case_id} has been identified as unclear_description by EmailDetect API. Please review it again.')

    return rag_info


if __name__ == '__main__':
    # # ## test
    # case_id = "123"
    # case_id = "A2009150609-0019"
    # case_id = "A2406049330-0010"
    case_id = "E25020003095-0001"
    a = search_cosmos_caseid_info(case_id)
    print(a)
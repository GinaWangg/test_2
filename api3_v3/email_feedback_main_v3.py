##### Application Insights (Azure Monitor) #####
from azure.identity import DefaultAzureCredential
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
import os

sub_id:str = os.getenv("MYAPP_AZURE_SUBSCRIPTION_ID") # type: ignore[assignment]
client = ApplicationInsightsManagementClient(credential=DefaultAzureCredential(), subscription_id=sub_id)
################################################

from azure.cosmos import CosmosClient
import traceback # for error handling

url_ = os.getenv("MYAPP_COSMOS_URL")
key_ = os.getenv("MYAPP_COSMOS_KEY")
database_name_:str = os.getenv("MYAPP_COSMOS_WRITE_DATABASE_NAME") # type: ignore[assignment]
if not url_ or not key_ or not database_name_:
    raise ValueError("Cosmos DB connection details are not set in environment variables.")

client = CosmosClient(
    url = url_,
    credential = key_,
    consistency_level='Session' 
    )

async def email_feedback_pre(case_id):
    # 檢查api2是否寫入資料
    database_name = database_name_
    container_name = 'kbRAG'
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    query = f"SELECT * FROM c WHERE c.case_id = '{case_id}' AND c.output_data != null" 
    results = container.query_items(query, enable_cross_partition_query=True)
    items = [item for item in results]
    if len(items) == 0:
        raise KeyError(f'Case id: {case_id} not found. Please confirm (1) if the case_id is entered correctly (2) execute API2 before API3.')
    else:
        return None

async def email_feedback(_id, case_id, agent_response_date, agent_response_info):

    try:
        input_data = {
            "case_id": case_id,
            "agent_response_date": agent_response_date,
            # "agent_response_info": []
            "agent_response_info": agent_response_info
            }
        
        # # 取得 agent_response_info 欄位清單，確保格式正確
        # for info in agent_response_info:
        #         validated_info = {
        #             "extract_type": info["extract_type"],
        #             "extract_type_num": info["extract_type_num"],
        #             "gpt_output": info["gpt_output"],
        #             "intent": info["intent"]
        #         }

        # # 如果存在 agent_response_kb，將其加入
        # if "agent_response_kb" in info:
        #     validated_info["agent_response_kb"] = info["agent_response_kb"]

        # # 如果存在 agent_response_content，將其加入
        # if "agent_response_content" in info:
        #     validated_info["agent_response_content"] = info["agent_response_content"]

        # input_data["agent_response_info"].append(validated_info)

        output = {
            "status": 200,
            "message": "Success",
            "output": {"case_id" : case_id}
        }

    except KeyError as e:
        output = {
            "status": 400,
            "message": e.args[0],
            "output": None
        }
        print(f'-------- (api3) case_id:{case_id}--------')
        print(f'error is {e.args[0]}')
        print(traceback.format_exc())
    except Exception as e:
        output = {
            "status": 400,
            "message": "Error",
            "output": None
        }
        print(f'-------- (api3) case_id:{case_id}--------')
        print(f'error is {e}')
        print(traceback.format_exc())
    finally:
         # 寫入資料
        database_name = database_name_
        container_name = 'emailFeedback'
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        new_item = {
            "id": _id,
            "case_id": case_id, 
            "input_data": input_data,
            "output_data": output,
        }

        container.upsert_item(new_item)
        
    return output


# # # 測試
# import asyncio

# if __name__ == '__main__':
#     # 測試資料
#     _id = "new_test"
#     case_id = "A2009150609-0019_test"
#     agent_response_date = 1712058385
#     agent_response_info = [
#         {
#             "extract_type": "split",
#             "extract_type_num": 1,
#             "gpt_output": "My premium phone shuts down automatically when I try to charge it.",
#             "intent": "warranty"
#         },
#         {
#             "extract_type": "split",
#             "extract_type_num": 2,
#             "gpt_output": "I heard a strange sound while riding my bike, and initially thought it was from the bike, but now I suspect it was from my phone.",
#             "intent": "Technical Support",
#             "agent_response_kb": 1011558
#         },
#         {
#             "extract_type": "split",
#             "extract_type_num": 3,
#             "gpt_output": "I have tried using different adaptors, but my phone still does not charge.",
#             "intent": "Technical Support",
#             "agent_response_kb": 1015484
#         }
#     ]

#     # 測試函式
#     async def test_email_feedback():
#         try:
#             result = await email_feedback(_id, case_id, agent_response_date, agent_response_info)
#             print("Function executed successfully. Output:")
#             print(result)
#         except Exception as e:
#             print("Function execution failed. Error:")
#             print(e)

#     # 啟動測試
#     asyncio.run(test_email_feedback())

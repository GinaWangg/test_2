import os

def write_cosmosDB(
        _id, 
        case_id, 
        input_data, 
        output_data,
        debug_data):

    new_item = {
        "id": _id,
        "case_id": case_id, 
        "api_version": "v3.2.2-gemini",   ## 和 confluence 上的版本號一致
        "input_data": input_data,
        "output_data": output_data,
        "debug_data": debug_data,
    }

    # 插入項目到 Cosmos DB
    print("Inserting item into Cosmos DB...")
    # print(new_item)


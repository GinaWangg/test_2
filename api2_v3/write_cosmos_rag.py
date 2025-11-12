from azure.cosmos import CosmosClient
import time
import os

def write_cosmosDB_rag(_id, case_id, input_data, output_data, error = None, error_detail = None):
    # ini_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_rag.ini')
    url_ = os.getenv("MYAPP_COSMOS_URL")
    key_ = os.getenv("MYAPP_COSMOS_KEY")
    database_name_ = os.getenv("MYAPP_COSMOS_WRITE_DATABASE_NAME")
    if not url_ or not key_ or not database_name_:
        raise ValueError("Cosmos DB connection details are not set in environment variables.")

    client = CosmosClient(
        url = url_,
        credential = key_,
        consistency_level='Session' 
        )

    database_name = database_name_
    container_name = 'kbRAG'
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    new_item = {
        # "id": f'{case_id}-{int(time.time())}{env}', 
        "id": _id,
        "case_id": case_id, 
        "input_data": input_data,
        "output_data": output_data,
        "error_message": error,
        "error_detail": error_detail
    }

    container.upsert_item(new_item)
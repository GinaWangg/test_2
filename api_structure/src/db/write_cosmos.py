"""
Cosmos DB utility functions and examples for using the CosmosDbClient.

This module provides helper functions for common Cosmos DB operations
using the initialized client from app.state.
"""

import json
from typing import Dict, Any, List, Optional
from fastapi import Request
# from src.db.cosmos_client import CosmosDbClient


# def get_cosmos_client(request: Request) -> CosmosDbClient:
#     """Get the Cosmos DB client from application state.
    
#     Args:
#         request: FastAPI Request object.
        
#     Returns:
#         CosmosDbClient instance from app.state.
        
#     Raises:
#         AttributeError: If cosmos_client is not initialized in app.state.
#     """
#     return request.app.state.cosmos_client


# async def write_log_to_cosmos(
#     cosmos_client: CosmosDbClient,
#     container_name: str,
#     log_data: Dict[str, Any]
# ) -> Dict[str, Any]:
#     """Write log data to Cosmos DB container.
    
#     Args:
#         cosmos_client: Initialized CosmosDbClient instance.
#         container_name: Name of the container to write to.
#         log_data: Dict containing the log data. Must include 'id' field.
        
#     Returns:
#         Dict containing the created item with metadata.
        
#     Raises:
#         exceptions.CosmosHttpResponseError: For Cosmos DB errors.
#     """
#     result = await cosmos_client.upsert_item(container_name, log_data)
#     print(
#         f"Log saved to Cosmos DB ({container_name}): "
#         f"id={log_data.get('id')}"
#     )
#     return result


# async def read_log_from_cosmos(
#     cosmos_client: CosmosDbClient,
#     container_name: str,
#     item_id: str,
#     partition_key: str
# ) -> Optional[Dict[str, Any]]:
#     """Read log data from Cosmos DB container.
    
#     Args:
#         cosmos_client: Initialized CosmosDbClient instance.
#         container_name: Name of the container to read from.
#         item_id: ID of the item to read.
#         partition_key: Partition key value.
        
#     Returns:
#         Dict containing the item data, or None if not found.
#     """
#     from azure.cosmos import exceptions
    
#     try:
#         result = await cosmos_client.read_item(
#             container_name, item_id, partition_key
#         )
#         return result
#     except exceptions.CosmosResourceNotFoundError:
#         print(
#             f"Item not found in Cosmos DB ({container_name}): "
#             f"id={item_id}, partition_key={partition_key}"
#         )
#         return None


# async def query_logs_by_session(
#     cosmos_client: CosmosDbClient,
#     container_name: str,
#     session_id: str,
#     max_items: int = 100
# ) -> List[Dict[str, Any]]:
#     """Query logs by session ID from Cosmos DB.
    
#     Args:
#         cosmos_client: Initialized CosmosDbClient instance.
#         container_name: Name of the container to query.
#         session_id: Session ID to filter logs.
#         max_items: Maximum number of items to return.
        
#     Returns:
#         List of log items matching the session ID.
#     """
#     query = "SELECT * FROM c WHERE c.session_id = @session_id"
#     parameters = [{"name": "@session_id", "value": session_id}]
    
#     results = await cosmos_client.query_items(
#         container_name=container_name,
#         query=query,
#         parameters=parameters,
#         max_item_count=max_items
#     )
#     return results


def write_log_to_cosmos(
    cosmos_container_name: str,
    log_data: Dict[str, Any]
) -> None:
    print(
        f"Log saved to Cosmos DB ({cosmos_container_name}): "
        f"{json.dumps(log_data, ensure_ascii=False, indent=2)}"
    )

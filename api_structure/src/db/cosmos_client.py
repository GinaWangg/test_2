'''
這是copilot 先產的一個版本 後續接正式資料再作驗證
'''

import os
from typing import Optional, Dict, Any, List
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from azure.cosmos.aio import ContainerProxy, DatabaseProxy


class CosmosDbClient:
    """Async client for Azure Cosmos DB with connection pooling.
    
    This class manages connection to Azure Cosmos DB and provides methods for
    CRUD operations with proper error handling.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        database_name: Optional[str] = None,
    ) -> None:
        """Initialize Cosmos DB client with Azure credentials.
        
        Args:
            endpoint: Azure Cosmos DB endpoint URL. If None, reads from
                MYAPP_COSMOS_ENDPOINT environment variable.
            key: Azure Cosmos DB primary key. If None, reads from
                MYAPP_COSMOS_KEY environment variable.
            database_name: Default database name. If None, reads from
                MYAPP_COSMOS_DATABASE environment variable.
        
        Raises:
            ValueError: If required credentials are not provided or found in
                environment.
        """
        self._endpoint = endpoint or os.getenv('MYAPP_COSMOS_ENDPOINT', '')
        self._key = key or os.getenv('MYAPP_COSMOS_KEY', '')
        self._database_name = (
            database_name or 
            os.getenv('MYAPP_COSMOS_DATABASE', '')
        )
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._validate_credentials()
        
    def _validate_credentials(self) -> None:
        """Validate that all required credentials are set.
        
        Raises:
            ValueError: If any required credential is missing.
        """
        if not self._endpoint or not self._key or not self._database_name:
            raise ValueError(
                "Cosmos DB client requires MYAPP_COSMOS_ENDPOINT, "
                "MYAPP_COSMOS_KEY, and MYAPP_COSMOS_DATABASE to be set."
            )
    
    async def initialize(self) -> None:
        """Initialize the Cosmos DB client connection.
        
        This should be called during application startup.
        """
        if self._client is not None:
            raise ValueError("Client is already initialized.")
            
        self._client = CosmosClient(self._endpoint, credential=self._key)
        self._database = self._client.get_database_client(self._database_name)
        print("Cosmos DB client initialized successfully")
    
    async def close(self) -> None:
        """Close the Cosmos DB client connection.
        
        This should be called during application shutdown.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._database = None
            print("Cosmos DB client closed successfully")
    
    def _get_container(self, container_name: str) -> ContainerProxy:
        """Get container client for specified container.
        
        Args:
            container_name: Name of the container.
            
        Returns:
            ContainerProxy instance for the specified container.
            
        Raises:
            ValueError: If client is not initialized.
        """
        if self._database is None:
            raise ValueError(
                "Client is not initialized. Call initialize() first."
            )
        return self._database.get_container_client(container_name)
    
    async def read_item(
        self, 
        container_name: str, 
        item_id: str, 
        partition_key: str
    ) -> Dict[str, Any]:
        """Read a single item from Cosmos DB.
        
        Args:
            container_name: Name of the container.
            item_id: ID of the item to read.
            partition_key: Partition key value.
            
        Returns:
            Dict containing the item data.
            
        Raises:
            exceptions.CosmosResourceNotFoundError: If item not found.
            exceptions.CosmosHttpResponseError: For other Cosmos DB errors.
        """
        container = self._get_container(container_name)
        try:
            response = await container.read_item(
                item=item_id, 
                partition_key=partition_key
            )
            return response
        except exceptions.CosmosResourceNotFoundError:
            raise
        except exceptions.CosmosHttpResponseError as e:
            print(
                f"Error reading item from Cosmos DB: "
                f"Status {e.status_code}, Message: {e.message}"
            )
            raise
    
    
    async def upsert_item(
        self, 
        container_name: str, 
        item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update an item in Cosmos DB.
        
        Args:
            container_name: Name of the container.
            item: Dict containing the item data. Must include 'id' field.
            
        Returns:
            Dict containing the upserted item with metadata.
            
        Raises:
            exceptions.CosmosHttpResponseError: For Cosmos DB errors.
        """
        container = self._get_container(container_name)
        try:
            response = await container.upsert_item(body=item)
            return response
        except exceptions.CosmosHttpResponseError as e:
            print(
                f"Error upserting item in Cosmos DB: "
                f"Status {e.status_code}, Message: {e.message}"
            )
            raise
    
    async def query_items(
        self,
        container_name: str,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
        max_item_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query items from Cosmos DB using SQL query.
        
        Args:
            container_name: Name of the container.
            query: SQL query string.
            parameters: Optional list of query parameters.
            partition_key: Optional partition key to limit query scope.
            max_item_count: Optional maximum number of items to return.
            
        Returns:
            List of items matching the query.
            
        Raises:
            exceptions.CosmosHttpResponseError: For Cosmos DB errors.
        """
        container = self._get_container(container_name)
        try:
            query_kwargs = {
                "query": query,
                "enable_cross_partition_query": partition_key is None
            }
            
            if parameters:
                query_kwargs["parameters"] = parameters
            if partition_key:
                query_kwargs["partition_key"] = partition_key
            if max_item_count:
                query_kwargs["max_item_count"] = max_item_count
            
            items = []
            async for item in container.query_items(**query_kwargs):
                items.append(item)
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(
                f"Error querying items from Cosmos DB: "
                f"Status {e.status_code}, Message: {e.message}"
            )
            raise

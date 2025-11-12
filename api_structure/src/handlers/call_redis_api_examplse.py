from src.clients.aiohttp_client import AiohttpClient
from core.timer import timed
from typing import Optional
import os
from api_structure.core.exception_handlers import AbortException

class CallRedisApiExamples:
    """Handler class for calling Redis API examples."""
    
    def __init__(
            self, 
            aiohttp_client: AiohttpClient,
            url: Optional[str] = None):
        """Initialize the handler with an Aiohttp client.
        
        Args:
            aiohttp_client: Initialized AiohttpClient instance.
        """
        self.aiohttp_client = aiohttp_client
        self._url = url or os.getenv('MYAPP_VECTOR_API_URL', '')

    
    async def _post_redis_api(
            self, 
            keyword: str) -> dict:
        """
        Post data to the Redis API endpoint.
        """
        data =[{
            "websiteCode": "all",
            "keyword": keyword,
            "productLine": "",
            "version": "5.0",
            "n": 1,
            "hide_min": 0,
            "hide_max": 1999
            }]

        async with self.aiohttp_client.session.post(
            url=self._url, 
            json=data) as resp:
            result = await resp.json()

        result_status = result.get("status", 400)
        if result_status != 200:
            raise AbortException(
                status=400,
                message=f"Redis API error",
                message_detail=f"Status: {result_status}, Response: {result}"
            )

        return result
    
    @timed(task_name = "call_redis_api_examples_run")
    async def run(self, keyword) -> dict:
        """
        Call the Redis API and return the result.
        """
        response = await self._post_redis_api(keyword)
        return response

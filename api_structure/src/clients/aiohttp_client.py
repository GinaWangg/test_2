"""Async HTTP client wrapper using aiohttp for connection pooling.

This module provides a reusable aiohttp ClientSession with connection pooling
that can be initialized at application startup and shared across requests.
"""

import aiohttp
from typing import Optional
from aiohttp import ClientTimeout


class AiohttpClient:
    """Async HTTP client wrapper for managing aiohttp ClientSession.
    
    This class manages a persistent aiohttp ClientSession with connection pooling
    for efficient HTTP requests across the application lifecycle.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        connector_limit: int = 100,
        connector_limit_per_host: int = 100
    ) -> None:
        """Initialize aiohttp client configuration.
        
        Args:
            timeout: Default timeout in seconds for requests. Defaults to 30.
            connector_limit: Total number of simultaneous connections. 
                Defaults to 100.
            connector_limit_per_host: Limit per host. Defaults to 100.
        """
        self._timeout = ClientTimeout(total=timeout)
        self._connector_limit = connector_limit
        self._connector_limit_per_host = connector_limit_per_host
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize the aiohttp ClientSession with connection pooling.
        
        This should be called during application startup.
        """
        if self._session is not None:
            raise ValueError("Client session is already initialized.")
        
        # 建立 connector 設定連線池
        connector = aiohttp.TCPConnector(
            limit=self._connector_limit,
            limit_per_host=self._connector_limit_per_host
        )
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self._timeout
        )

        print(f"Aiohttp client initialized successfully with connection pool")

    async def close(self) -> None:
        """Close the aiohttp ClientSession.
        
        This should be called during application shutdown.
        """
        if self._session is not None:
            await self._session.close()
            self._session = None
            print("Aiohttp client closed successfully")
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the active ClientSession.
        
        Returns:
            The active aiohttp ClientSession.
            
        Raises:
            RuntimeError: If session is not initialized.
        """
        if self._session is None:
            raise RuntimeError(
                "Client session is not initialized. "
                "Call initialize() first."
            )
        return self._session
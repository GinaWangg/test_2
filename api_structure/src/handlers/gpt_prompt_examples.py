"""GPT prompt examples for various use cases."""

from api_structure.src.clients.gpt import GptClient
from api_structure.core.timer import timed


class GptTaskHandler:
    """Handler class for GPT prompt examples."""
    
    def __init__(self, gpt_client: GptClient):
        """Initialize the handler with a GPT client.
        
        Args:
            gpt_client: Initialized GptClient instance.
        """
        self.gpt_client = gpt_client
    
    async def _simple_hello_world_example(self) -> dict:
        """Simple example: AI customer service responding with hello world.
        
        Returns:
            Response from GPT model.
        """
        sys_prompt = '''
        你是一個ai客服
        回應都要有 "ai response"
        用 json format 回應
        '''
        user_prompt = '回應給我 hello world'
        
        response = await self.gpt_client.call_with_prompts(
            system_prompt=sys_prompt,
            user_prompt=user_prompt
        )
        
        return response
    
    @timed(task_name = "gpt_task_handler_run")
    async def run(self) -> str:
        """
        這裡面可以寫作一些 gpt return 後的處理邏輯
        """
        response = await self._simple_hello_world_example()
        result = response.get('ai response', 'No ai response found')

        return result

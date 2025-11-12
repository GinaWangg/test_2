import random
import asyncio
from api_structure.core.exception_handlers import AbortException, WarningException
from api_structure.core.timer import timed

@timed(task_name="example_abort")
async def example_abort(text: str) -> str:
    await asyncio.sleep(0.1)

    rr = random.random()
    if rr < 1:  # 控制模擬 錯誤 需要結束的錯誤
        raise AbortException(
            status=400, 
            message="example_abort failed due to invalid input"
        )
    
    # 成功的翻譯（示範）
    return f"(abort success) {text}"
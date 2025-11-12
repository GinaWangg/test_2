import random
import asyncio
from api_structure.core.exception_handlers import WarningException
from api_structure.core.timer import timed

@timed(task_name="example_warning")
async def example_warning(text: str) -> str:
    await asyncio.sleep(0.1)

    rr = random.random()
    if rr < 0: # 控制模擬 錯誤 需要警告的錯誤
        raise WarningException(
            message="example_warning failed",
            default_result='warning fallback',
            task_name="example_warning"
        )
    
    # 成功的翻譯（示範）
    return f"(warning success) {text}"


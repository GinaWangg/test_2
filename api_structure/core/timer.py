import functools
from api_structure.core.exception_handlers import WarningException
from api_structure.core.logger import get_log_context
import time
from opentelemetry import trace
tracer = trace.get_tracer(__name__)


def timed(task_name: str):
    """
    裝飾器 : 統一處理可恢復的錯誤 + function 計時
    當函數拋出 WarningException 時，會自動記錄錯誤日誌並返回預設值
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(func.__name__) as span:
                try:
                    s_time = time.time()
                    result = await func(*args, **kwargs)
                    return result
                except WarningException as e:
                    ctx = get_log_context()
                    ctx.error_log.append({
                        "event": e.task_name or task_name,
                        "message": e.message,
                        "metadata": {"args": args, "kwargs": kwargs}
                    })
                    span.set_attribute("event", e.task_name or task_name)
                    span.set_attribute("message", e.message)
                    span.set_attribute("args", str(args))
                    return e.default_result
                finally:
                    elapsed = time.time() - s_time
                    # print(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return wrapper
    return decorator
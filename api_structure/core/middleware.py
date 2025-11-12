from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import json
from api_structure.core.logger import create_log_context, set_end_time
from api_structure.src.db.write_cosmos import write_log_to_cosmos
from api_structure.core.exception_handlers import AbortException
from traceback import format_exc

# 改成你專案的名稱
PATH_TO_CONTAINER: dict[str, str] = {    
    "/v1/test_gpt": "test_gpt",
    "/v1/test_api": "test_api",
    "/v1/test_aiohttp": "test_aiohttp",
}

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 需要紀錄 log 的路徑
        skip_paths = list(PATH_TO_CONTAINER.keys())
        if request.url.path not in skip_paths:
            return await call_next(request)  # 直接跳過 log
        
        raw = await request.body()
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            body = {"_raw": raw.decode("utf-8", errors="ignore")}

        # 建立 log context
        log_ctx = create_log_context(input_data=body)
        request.state.log_context = log_ctx

        # 重要：把 body 回填給 FastAPI，否則 Pydantic 讀不到
        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}
        request._receive = receive
        
        try:
            response = await call_next(request)
            
            # 因為 StreamingResponse 所以擷取output比較麻煩
            response_body = b""
            if isinstance(response, StreamingResponse):
                # 收集所有 chunks
                chunks = []
                async for chunk in response.body_iterator:
                    if isinstance(chunk, bytes):
                        chunks.append(chunk)
                    elif isinstance(chunk, (bytearray, memoryview)):
                        chunks.append(bytes(chunk))
                    elif isinstance(chunk, str):
                        chunks.append(chunk.encode('utf-8'))
                    else:
                        chunks.append(str(chunk).encode('utf-8'))
                
                response_body = b''.join(chunks)
                
                # 重建 StreamingResponse
                async def generate():
                    yield response_body
                
                response = StreamingResponse(
                    generate(),
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type
                )
            
            # 嘗試解析和 print 響應內容
            if response_body:
                try:
                    log_ctx.output_data = json.loads(
                        response_body.decode("utf-8"))
                except Exception:
                    log_ctx.output_data = {
                        "raw_body": response_body.decode(
                            "utf-8", 
                            errors="ignore")
                            }
            
            # 設定結束時間
            set_end_time()
            
            # 統一返回格式
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "status": response.status_code,
                    "message": "Success" if response.status_code == 200 else "Error",
                    "data": log_ctx.output_data
                }
            )
        
        # 預期的錯誤，直接丟給 FastAPI 的 exception handler
        except AbortException as ce:
            log_ctx.error_log.append({
                "event": "abort_exception",
                "message": str(ce),
                "detail": ce.message_detail,
                "trace": format_exc(),
            })
            set_end_time()
            return JSONResponse(
                status_code=ce.status,
                content={
                    "status": ce.status, 
                    "message": ce.message},
            )
        
        # 非預期的錯誤 寫入log 結束這個request
        except Exception as e:
            log_ctx.error_log.append({
                "event": "unhandled_exception",
                "message": str(e),
                "trace": format_exc(),
            })
            set_end_time()
            return JSONResponse(
                status_code=400,
                content={"status": 400, "message": "ERROR"},
            )
        
        # 無論如何都嘗試把 log 寫入 Cosmos
        finally:
            logs_ = log_ctx.to_dict()
            if not logs_:
                logs_ = {"message": "No logs captured"}

            container_name = PATH_TO_CONTAINER.get(request.url.path)
            if container_name:
                write_log_to_cosmos(container_name, logs_)
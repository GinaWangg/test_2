from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


# ------------- 不能繼續執行的錯誤 ---------------------------------------------
class AbortException(Exception):
    def __init__(
            self, 
            status: int, 
            message: str, 
            message_detail: str = ""):
        self.status = int(status)
        self.message = str(message)
        self.message_detail = str(message_detail)
        super().__init__(message)

# ------------- 可以繼續執行的錯誤 ---------------------------------------------
class WarningException(Exception):
    def __init__(self, 
                 message: str, 
                 default_result: str, 
                 task_name: str):
        self.message = str(message)
        self.default_result = default_result
        self.task_name = task_name
        super().__init__(message)


# ------------- HTTPException 特別處理器 ---------------------------------------
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 422 and "reviewType" in str(exc.detail):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "message": "Failed. Invalid reviewType value in input."
            }
        )
    
    # 其他默認的錯誤處理器
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "message": "Failed. An unexpected error occurred."
        }
    )

# ------------- 全域錯誤處理器 -------------------------------------------------
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": "Failed. An unexpected error occurred"
        }
    )


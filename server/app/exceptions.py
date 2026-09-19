from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

async def rfc7807_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler returning standard RFC 7807 Problem Details JSON format."""
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
        title = "HTTP Exception"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = str(exc) if str(exc) else "An unexpected internal server error occurred."
        title = "Internal Server Error"

    problem_details = {
        "type": f"https://httpstatuses.io/{status_code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path)
    }

    return JSONResponse(status_code=status_code, content=problem_details)

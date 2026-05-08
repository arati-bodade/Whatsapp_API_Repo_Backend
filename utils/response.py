from typing import Any, Dict, Optional
from fastapi import HTTPException, status


def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Standard success response format."""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response


def error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    """Standard error response format."""
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message}
    )

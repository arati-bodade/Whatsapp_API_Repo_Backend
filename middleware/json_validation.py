from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import json
import logging

logger = logging.getLogger(__name__)

async def json_validation_middleware(request: Request, call_next):
    """Middleware to validate JSON and provide better error messages."""
    
    if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
        try:
            # Get raw body
            body = await request.body()
            
            # Check for control characters
            for i, char in enumerate(body):
                if char < 32 and char not in [9, 10, 13]:  # Not tab, newline, carriage return
                    logger.warning(f"Invalid control character at position {i}: {char}")
                    return JSONResponse(
                        status_code=422,
                        content={
                            "detail": [
                                {
                                    "type": "json_invalid",
                                    "loc": ["body", i],
                                    "msg": f"Invalid control character at position {i}",
                                    "input": str(body),
                                    "ctx": {"error": f"Control character {char} found"}
                                }
                            ]
                        }
                    )
            
            # Try to parse JSON
            if body:
                json.loads(body.decode('utf-8'))
                
        except UnicodeDecodeError as e:
            return JSONResponse(
                status_code=422,
                content={
                    "detail": [
                        {
                            "type": "unicode_error",
                            "loc": ["body"],
                            "msg": f"Unicode decode error: {str(e)}",
                            "input": str(body)[:100]
                        }
                    ]
                }
            )
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=422,
                content={
                    "detail": [
                        {
                            "type": "json_invalid",
                            "loc": ["body", e.pos],
                            "msg": f"JSON decode error: {str(e)}",
                            "input": str(body)[:100],
                            "ctx": {"error": str(e)}
                        }
                    ]
                }
            )
        except Exception as e:
            logger.error(f"JSON validation error: {str(e)}")
            return JSONResponse(
                status_code=422,
                content={
                    "detail": [
                        {
                            "type": "validation_error",
                            "loc": ["body"],
                            "msg": f"Validation error: {str(e)}",
                            "input": str(body)[:100]
                        }
                    ]
                }
            )
    
    response = await call_next(request)
    return response

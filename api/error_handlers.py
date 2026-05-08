"""
🧨 STEP 6: API ERROR HANDLING

Replace raw 500 errors with meaningful API responses
Ensure frontend receives proper error messages instead of empty {}
"""
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from psycopg2 import errors
import uuid

logger = logging.getLogger(__name__)

async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle database errors with meaningful messages
    """
    logger.error(f"Database error: {exc}")
    
    # 🔥 UUID ERROR HANDLING
    if isinstance(exc, ProgrammingError):
        error_str = str(exc)
        if "invalid input syntax for type uuid" in error_str:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Invalid UUID format",
                    "message": "Device ID or User ID is not a valid UUID format",
                    "details": "Please check that all IDs are valid UUIDs"
                }
            )
        elif "foreign key" in error_str.lower() and "busi_users" in error_str:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Database foreign key error",
                    "message": "Database schema issue detected. Please contact administrator.",
                    "details": "Foreign key constraint violation"
                }
            )
        elif "does not exist" in error_str:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Database schema error",
                    "message": "Required database column or table is missing. Please run database migrations.",
                    "details": str(exc)
                }
            )
        elif "column" in error_str.lower() and "does not exist" in error_str.lower():
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Missing database column",
                    "message": "Database schema is outdated. Please run: alembic upgrade head",
                    "details": str(exc)
                }
            )
    
    # Generic database error
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Database operation failed",
            "message": "A database error occurred. Please try again later.",
            "details": str(exc) if logger.isEnabledFor(logging.DEBUG) else "Database error details"
        }
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with proper formatting
    """
    logger.error(f"Validation error: {exc}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )

async def attribute_error_handler(request: Request, exc: AttributeError):
    """
    Handle attribute errors (missing model attributes)
    """
    logger.error(f"Attribute error: {exc}")
    
    error_msg = str(exc)
    
    if "status_column" in error_msg:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Trigger configuration error",
                "message": "Trigger is missing required configuration. Please recreate the trigger.",
                "details": "Missing status_column in trigger configuration"
            }
        )
    elif "phone_column" in error_msg:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Trigger configuration error",
                "message": "Trigger is missing phone column configuration. Please recreate the trigger.",
                "details": "Missing phone_column in trigger configuration"
            }
        )
    elif "last_processed_row" in error_msg:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Trigger configuration error",
                "message": "Trigger configuration is outdated. Please recreate the trigger.",
                "details": "Missing last_processed_row in trigger configuration"
            }
        )
    
    # Generic attribute error
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Configuration error",
            "message": "A configuration error occurred. Please check your setup.",
            "details": str(exc)
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions with proper logging
    """
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "details": str(exc) if logger.isEnabledFor(logging.DEBUG) else "Error details hidden"
        }
    )

def setup_error_handlers(app):
    """
    Setup all error handlers for the FastAPI app
    """
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(AttributeError, attribute_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ Error handlers setup complete")

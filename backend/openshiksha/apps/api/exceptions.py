"""
Custom exception handlers for API
"""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response format
        custom_response_data = {"error": True, "message": str(exc), "details": response.data}
        response.data = custom_response_data

    return response

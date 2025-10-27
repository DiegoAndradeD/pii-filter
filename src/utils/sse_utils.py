"""
Utility module for creating Server-Sent Events (SSE) formatted strings
for streaming responses in the API.
"""

import json


def create_sse_event(data: dict) -> str:
    """
    Creates a Server-Sent Event formatted string.

    Args:
        data: Dictionary containing the event data.

    Returns:
        SSE formatted string.
    """
    return f"data: {json.dumps(data)}\n\n"

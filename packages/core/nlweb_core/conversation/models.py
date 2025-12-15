# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Data models for conversation storage.

WARNING: This code is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from nlweb_core.protocol.models import AskRequest, ResultObject


class ConversationMessage(BaseModel):
    """
    A message in a conversation (user query or assistant response).

    This model stores the complete context of a message exchange, including
    the full v0.54 protocol request for user messages and result objects
    for assistant responses.
    """

    message_id: str = Field(
        ...,
        description="Unique identifier for this message"
    )

    conversation_id: str = Field(
        ...,
        description="Identifier linking this message to a conversation"
    )

    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'"
    )

    timestamp: datetime = Field(
        ...,
        description="When this message was created"
    )

    # For user messages - store the complete request
    request: Optional[AskRequest] = Field(
        None,
        description="Full v0.54 AskRequest for user messages"
    )

    # For assistant messages - store the results
    results: Optional[List[ResultObject]] = Field(
        None,
        description="Result objects returned for assistant messages"
    )

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (site, response_format, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123456",
                "conversation_id": "conv_abc123",
                "role": "user",
                "timestamp": "2025-01-15T10:30:00Z",
                "request": {
                    "query": {"text": "best pizza in Seattle"},
                    "prefer": {"streaming": True, "response_format": "conv_search"}
                },
                "metadata": {"site": "yelp.com"}
            }
        }

# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Conversation storage interface and client.

WARNING: This code is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import importlib

from nlweb_core.conversation.models import ConversationMessage
from nlweb_core.config import CONFIG


class ConversationStorageInterface(ABC):
    """Abstract interface for conversation storage backends."""

    @abstractmethod
    async def store_message(self, message: ConversationMessage) -> None:
        """
        Store a conversation message.

        Args:
            message: The message to store
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[ConversationMessage]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of messages to return

        Returns:
            List of messages ordered by timestamp
        """
        pass

    @abstractmethod
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[str]:
        """
        Get conversation IDs for a specific user.

        Args:
            user_id: The user ID
            limit: Maximum number of conversation IDs to return

        Returns:
            List of conversation IDs ordered by most recent activity
        """
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete all messages in a conversation.

        Args:
            conversation_id: The conversation ID to delete
        """
        pass


class ConversationStorageClient:
    """
    Client that routes to appropriate storage backend based on configuration.
    """

    def __init__(self, backend: Optional[ConversationStorageInterface] = None):
        """
        Initialize storage client.

        Args:
            backend: Optional backend override for testing. If not provided,
                    creates backend from CONFIG.conversation_storage
        """
        if backend is not None:
            self.backend = backend
        else:
            self.backend = self._create_backend_from_config()

    def _create_backend_from_config(self) -> ConversationStorageInterface:
        """
        Create the appropriate storage backend from configuration.

        Returns:
            Storage backend instance

        Raises:
            ValueError: If backend type is unknown or not enabled
        """
        if not hasattr(CONFIG, 'conversation_storage'):
            raise ValueError("No conversation_storage configuration found")

        storage_config = CONFIG.conversation_storage

        if not storage_config.enabled:
            raise ValueError("Conversation storage is not enabled in configuration")

        backend_type = storage_config.type

        # Map backend types to modules
        backend_map = {
            "memory": "nlweb_core.conversation.backends.memory.MemoryStorage",
            "qdrant": "nlweb_core.conversation.backends.qdrant.QdrantStorage",
        }

        if backend_type not in backend_map:
            raise ValueError(f"Unknown storage backend: {backend_type}")

        # Import and instantiate the backend
        module_path, class_name = backend_map[backend_type].rsplit(".", 1)
        module = importlib.import_module(module_path)
        backend_class = getattr(module, class_name)

        # Pass the storage config to the backend
        return backend_class(storage_config)

    async def store_message(self, message: ConversationMessage) -> None:
        """Store a message."""
        await self.backend.store_message(message)

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[ConversationMessage]:
        """Get messages for a conversation."""
        return await self.backend.get_messages(conversation_id, limit)

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[str]:
        """Get conversation IDs for a user."""
        return await self.backend.get_user_conversations(user_id, limit)

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation."""
        await self.backend.delete_conversation(conversation_id)

"""Entity conversion utilities for different Telegram libraries."""

from typing import List
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class EntityConverter:
    """Converts between different entity formats."""

    @staticmethod
    def telethon_to_dict(entities: List) -> List[dict]:
        """
        Convert Telethon entities to dictionary format.

        Args:
            entities: List of Telethon MessageEntity objects

        Returns:
            List of entity dictionaries
        """
        result = []
        for entity in entities:
            entity_dict = {
                "type": entity.__class__.__name__,
                "offset": entity.offset,
                "length": entity.length,
            }

            # Add URL for text links
            if hasattr(entity, "url") and entity.url:
                entity_dict["url"] = entity.url

            # Add language for pre-formatted code
            if hasattr(entity, "language") and entity.language:
                entity_dict["language"] = entity.language

            result.append(entity_dict)

        return result

    @staticmethod
    def dict_to_telethon(entity_dicts: List[dict]) -> List:
        """
        Convert dictionary entities to Telethon format.

        Args:
            entity_dicts: List of entity dictionaries

        Returns:
            List of Telethon MessageEntity objects
        """
        from telethon.tl.types import (
            MessageEntityBold,
            MessageEntityItalic,
            MessageEntityCode,
            MessageEntityPre,
            MessageEntityTextUrl,
            MessageEntityStrike,
            MessageEntityUnderline,
            MessageEntityBlockquote,
            MessageEntitySpoiler,
        )

        entity_map = {
            "MessageEntityBold": MessageEntityBold,
            "MessageEntityItalic": MessageEntityItalic,
            "MessageEntityCode": MessageEntityCode,
            "MessageEntityPre": MessageEntityPre,
            "MessageEntityTextUrl": MessageEntityTextUrl,
            "MessageEntityStrike": MessageEntityStrike,
            "MessageEntityUnderline": MessageEntityUnderline,
            "MessageEntityBlockquote": MessageEntityBlockquote,
            "MessageEntitySpoiler": MessageEntitySpoiler,
        }

        result = []
        for entity_dict in entity_dicts:
            entity_type = entity_dict.get("type")
            entity_class = entity_map.get(entity_type)

            if not entity_class:
                logger.warning(f"Unknown entity type: {entity_type}")
                continue

            # Create entity with basic parameters
            kwargs = {
                "offset": entity_dict.get("offset", 0),
                "length": entity_dict.get("length", 0),
            }

            # Add optional parameters
            if entity_type == "MessageEntityTextUrl":
                kwargs["url"] = entity_dict.get("url", "")
            elif entity_type == "MessageEntityPre":
                kwargs["language"] = entity_dict.get("language", "")

            try:
                entity = entity_class(**kwargs)
                result.append(entity)
            except Exception as e:
                logger.error(f"Failed to create entity {entity_type}: {e}")

        return result

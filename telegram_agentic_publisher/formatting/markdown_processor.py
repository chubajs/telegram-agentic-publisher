"""Markdown processing for Telegram formatting."""

import re
from typing import List, Tuple, Optional
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
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MarkdownProcessor:
    """Processes markdown text for Telegram."""

    @staticmethod
    def fix_telethon_markdown(text: str) -> str:
        """
        Fix markdown formatting for Telethon compatibility.

        Args:
            text: Raw markdown text

        Returns:
            Fixed markdown text
        """
        if not text:
            return ""

        # Fix nested formatting issues
        text = re.sub(r'\*{3,}', '**', text)  # Fix triple or more asterisks
        text = re.sub(r'_{3,}', '__', text)  # Fix triple or more underscores
        text = re.sub(r'~{3,}', '~~', text)  # Fix triple or more tildes

        # Fix markdown links with special characters
        def fix_link(match):
            text_part = match.group(1)
            url_part = match.group(2)
            # Escape special characters in URL
            url_part = url_part.replace('(', '%28').replace(')', '%29')
            return f"[{text_part}]({url_part})"

        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', fix_link, text)

        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Ensure code blocks are properly formatted
        text = re.sub(r'```(\w*)\n', r'```\1\n', text)

        return text

    @staticmethod
    def parse_markdown_entities(text: str) -> Tuple[str, List]:
        """
        Parse markdown and convert to Telegram entities.

        Args:
            text: Markdown formatted text

        Returns:
            Tuple of (plain_text, entities_list)
        """
        if not text:
            return "", []

        # Track entities with their positions
        entities = []
        plain_text = text
        offset_adjustment = 0

        # Process inline code first (to avoid conflicts)
        code_pattern = r'`([^`]+)`'
        for match in reversed(list(re.finditer(code_pattern, plain_text))):
            start = match.start() - offset_adjustment
            end = match.end() - offset_adjustment
            code_text = match.group(1)

            # Calculate UTF-16 positions
            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(code_text)

            entities.append(MessageEntityCode(utf16_start, utf16_length))

            # Replace in plain text
            plain_text = plain_text[:match.start()] + code_text + plain_text[match.end():]
            offset_adjustment += 2  # Account for removed backticks

        # Process bold text
        bold_pattern = r'\*\*([^*]+)\*\*'
        for match in reversed(list(re.finditer(bold_pattern, plain_text))):
            start = match.start()
            bold_text = match.group(1)

            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(bold_text)

            entities.append(MessageEntityBold(utf16_start, utf16_length))

            plain_text = plain_text[:match.start()] + bold_text + plain_text[match.end():]

        # Process italic text
        italic_pattern = r'(?<!\*)\*([^*]+)\*(?!\*)|_([^_]+)_'
        for match in reversed(list(re.finditer(italic_pattern, plain_text))):
            start = match.start()
            italic_text = match.group(1) or match.group(2)

            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(italic_text)

            entities.append(MessageEntityItalic(utf16_start, utf16_length))

            plain_text = plain_text[:match.start()] + italic_text + plain_text[match.end():]

        # Process strikethrough text
        strike_pattern = r'~~([^~]+)~~'
        for match in reversed(list(re.finditer(strike_pattern, plain_text))):
            start = match.start()
            strike_text = match.group(1)

            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(strike_text)

            entities.append(MessageEntityStrike(utf16_start, utf16_length))

            plain_text = plain_text[:match.start()] + strike_text + plain_text[match.end():]

        # Process underline text
        underline_pattern = r'__([^_]+)__'
        for match in reversed(list(re.finditer(underline_pattern, plain_text))):
            start = match.start()
            underline_text = match.group(1)

            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(underline_text)

            entities.append(MessageEntityUnderline(utf16_start, utf16_length))

            plain_text = plain_text[:match.start()] + underline_text + plain_text[match.end():]

        # Process links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in reversed(list(re.finditer(link_pattern, plain_text))):
            start = match.start()
            link_text = match.group(1)
            url = match.group(2)

            # Decode URL if needed
            url = url.replace('%28', '(').replace('%29', ')')

            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(link_text)

            entities.append(MessageEntityTextUrl(utf16_start, utf16_length, url=url))

            plain_text = plain_text[:match.start()] + link_text + plain_text[match.end():]

        # Process code blocks
        code_block_pattern = r'```(?:\w*\n)?([\s\S]*?)```'
        for match in reversed(list(re.finditer(code_block_pattern, plain_text))):
            start = match.start()
            code_text = match.group(1).strip()

            utf16_start = MarkdownProcessor._calculate_utf16_offset(plain_text[:start])
            utf16_length = MarkdownProcessor._calculate_utf16_length(code_text)

            entities.append(MessageEntityPre(utf16_start, utf16_length, language=''))

            plain_text = plain_text[:match.start()] + code_text + plain_text[match.end():]

        # Process blockquotes
        blockquote_lines = []
        lines = plain_text.split('\n')
        new_lines = []

        for i, line in enumerate(lines):
            if line.startswith('>'):
                # Remove the > prefix
                clean_line = line[1:].strip()
                new_lines.append(clean_line)

                # Track position for entity
                line_start = len('\n'.join(new_lines[:i]))
                utf16_start = MarkdownProcessor._calculate_utf16_offset('\n'.join(new_lines[:i]))
                utf16_length = MarkdownProcessor._calculate_utf16_length(clean_line)

                entities.append(MessageEntityBlockquote(utf16_start, utf16_length))
            else:
                new_lines.append(line)

        if blockquote_lines:
            plain_text = '\n'.join(new_lines)

        # Sort entities by offset (important for Telegram)
        entities.sort(key=lambda e: e.offset)

        return plain_text.strip(), entities

    @staticmethod
    def _calculate_utf16_offset(text: str) -> int:
        """
        Calculate UTF-16 offset for text.

        Args:
            text: Text before the entity

        Returns:
            UTF-16 offset
        """
        return len(text.encode('utf-16-le')) // 2

    @staticmethod
    def _calculate_utf16_length(text: str) -> int:
        """
        Calculate UTF-16 length for text.

        Args:
            text: Entity text

        Returns:
            UTF-16 length
        """
        return len(text.encode('utf-16-le')) // 2

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape special markdown characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        # Characters that need escaping in markdown
        special_chars = ['*', '_', '~', '`', '[', ']', '(', ')', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

        for char in special_chars:
            text = text.replace(char, f'\\{char}')

        return text
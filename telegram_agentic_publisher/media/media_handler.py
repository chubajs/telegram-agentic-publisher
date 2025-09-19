"""Media handling for Telegram posts."""

import tempfile
from pathlib import Path
from typing import List, Any, Optional, Tuple
import aiohttp
from PIL import Image
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MediaHandler:
    """Handles media processing for Telegram posts."""

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize media handler.

        Args:
            cache_path: Path for caching media files
        """
        self.cache_path = cache_path or Path(tempfile.gettempdir()) / "telegram_media_cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.temp_files: List[Path] = []

    async def prepare_media(
        self, media_items: List[Any], max_items: int = 10
    ) -> Tuple[List[Path], List[str]]:
        """
        Prepare media items for upload.

        Args:
            media_items: List of media items (URLs, file paths, or dicts with 'url' key)
            max_items: Maximum number of items to process

        Returns:
            Tuple of (local_file_paths, media_types)
        """
        prepared_files = []
        media_types = []

        # Limit to max items (Telegram limit is 10)
        items_to_process = media_items[:max_items]

        for item in items_to_process:
            try:
                file_path, media_type = await self._process_media_item(item)
                if file_path:
                    prepared_files.append(file_path)
                    media_types.append(media_type)
            except Exception as e:
                logger.warning(f"Failed to process media item: {e}")
                continue

        return prepared_files, media_types

    async def _process_media_item(self, item: Any) -> Tuple[Optional[Path], str]:
        """
        Process a single media item.

        Args:
            item: Media item (URL, file path, or dict)

        Returns:
            Tuple of (file_path, media_type)
        """
        # Extract URL or path from item
        if isinstance(item, dict):
            url_or_path = item.get("url") or item.get("path") or item.get("file")
            media_type = item.get("type", "photo")
        else:
            url_or_path = str(item)
            media_type = self._guess_media_type(url_or_path)

        if not url_or_path:
            return None, "unknown"

        # Check if it's a URL or local file
        if url_or_path.startswith(("http://", "https://")):
            file_path = await self._download_media(url_or_path)
        else:
            file_path = Path(url_or_path)
            if not file_path.exists():
                logger.warning(f"Local file not found: {file_path}")
                return None, media_type

        # Optimize image if needed
        if media_type == "photo" and file_path:
            file_path = await self._optimize_image(file_path)

        return file_path, media_type

    async def _download_media(self, url: str) -> Optional[Path]:
        """
        Download media from URL.

        Args:
            url: Media URL

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Generate cache filename from URL
            cache_filename = self._get_cache_filename(url)
            cache_file = self.cache_path / cache_filename

            # Check if already cached
            if cache_file.exists():
                logger.debug(f"Using cached media: {cache_file}")
                return cache_file

            # Download the file
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download {url}: HTTP {response.status}")
                        return None

                    # Save to cache
                    content = await response.read()
                    cache_file.write_bytes(content)
                    logger.info(f"Downloaded media to {cache_file}")

                    # Track for cleanup
                    self.temp_files.append(cache_file)
                    return cache_file

        except Exception as e:
            logger.error(f"Error downloading media from {url}: {e}")
            return None

    async def _optimize_image(self, image_path: Path) -> Path:
        """
        Optimize image for Telegram upload.

        Args:
            image_path: Path to image file

        Returns:
            Path to optimized image (may be the same if no optimization needed)
        """
        try:
            # Open image
            with Image.open(image_path) as img:
                # Check if optimization is needed
                max_dimension = 2560  # Telegram's recommended max
                width, height = img.size

                if width <= max_dimension and height <= max_dimension:
                    return image_path  # No optimization needed

                # Calculate new dimensions
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))

                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Save optimized image
                optimized_path = image_path.with_suffix(".optimized.jpg")
                img_resized.save(optimized_path, "JPEG", quality=95, optimize=True)

                logger.info(f"Optimized image from {width}x{height} to {new_width}x{new_height}")

                # Track for cleanup
                self.temp_files.append(optimized_path)
                return optimized_path

        except Exception as e:
            logger.warning(f"Failed to optimize image: {e}")
            return image_path  # Return original if optimization fails

    def _get_cache_filename(self, url: str) -> str:
        """
        Generate cache filename from URL.

        Args:
            url: Media URL

        Returns:
            Cache filename
        """
        import hashlib

        # Create hash of URL
        url_hash = hashlib.md5(url.encode()).hexdigest()

        # Get file extension from URL
        extension = Path(url.split("?")[0]).suffix or ".tmp"

        return f"{url_hash}{extension}"

    def _guess_media_type(self, url_or_path: str) -> str:
        """
        Guess media type from URL or file path.

        Args:
            url_or_path: URL or file path

        Returns:
            Media type (photo, video, document)
        """
        # Remove query parameters if URL
        clean_path = url_or_path.split("?")[0].lower()

        # Image extensions
        if any(clean_path.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]):
            return "photo"

        # Video extensions
        if any(clean_path.endswith(ext) for ext in [".mp4", ".avi", ".mov", ".webm", ".mkv"]):
            return "video"

        # Default to document
        return "document"

    async def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")

        self.temp_files.clear()

    def clear_cache(self):
        """Clear the entire media cache."""
        try:
            for cache_file in self.cache_path.iterdir():
                if cache_file.is_file():
                    cache_file.unlink()
            logger.info("Media cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear media cache: {e}")

    def get_cache_size(self) -> int:
        """
        Get total size of cached media in bytes.

        Returns:
            Total cache size in bytes
        """
        total_size = 0
        try:
            for cache_file in self.cache_path.iterdir():
                if cache_file.is_file():
                    total_size += cache_file.stat().st_size
        except Exception as e:
            logger.error(f"Failed to calculate cache size: {e}")
        return total_size

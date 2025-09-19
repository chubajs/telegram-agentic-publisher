"""Media downloader with retry and optimization support."""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MediaDownloader:
    """Downloads media files with retry logic and optimization."""

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        """
        Initialize media downloader.

        Args:
            max_retries: Maximum number of download retries
            timeout: Download timeout in seconds
        """
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def download(
        self,
        url: str,
        output_path: Optional[Path] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Path]:
        """
        Download a file from URL with retry logic.

        Args:
            url: URL to download from
            output_path: Optional output file path
            headers: Optional HTTP headers

        Returns:
            Path to downloaded file or None if failed
        """
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

        for attempt in range(self.max_retries):
            try:
                return await self._download_attempt(url, output_path, headers)
            except aiohttp.ClientError as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to download {url} after {self.max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error downloading {url}: {e}")
                return None

        return None

    async def _download_attempt(
        self,
        url: str,
        output_path: Optional[Path],
        headers: Optional[Dict[str, str]],
    ) -> Path:
        """
        Single download attempt.

        Args:
            url: URL to download from
            output_path: Optional output file path
            headers: Optional HTTP headers

        Returns:
            Path to downloaded file
        """
        async with self.session.get(url, headers=headers) as response:
            response.raise_for_status()

            # Generate output path if not provided
            if not output_path:
                import tempfile

                suffix = Path(url.split("?")[0]).suffix or ".tmp"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    output_path = Path(tmp_file.name)

            # Download in chunks for progress tracking
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192

            with open(output_path, "wb") as file:
                async for chunk in response.content.iter_chunked(chunk_size):
                    file.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (chunk_size * 100) == 0:  # Log every 800KB
                            logger.debug(f"Download progress: {progress:.1f}%")

            logger.info(f"Downloaded {url} to {output_path} ({downloaded} bytes)")
            return output_path

    async def get_file_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get file information without downloading.

        Args:
            url: URL to check

        Returns:
            Dictionary with file info or None if failed
        """
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

        try:
            async with self.session.head(url) as response:
                response.raise_for_status()

                return {
                    "size": int(response.headers.get("content-length", 0)),
                    "content_type": response.headers.get("content-type", "unknown"),
                    "last_modified": response.headers.get("last-modified"),
                    "etag": response.headers.get("etag"),
                    "status": response.status,
                }
        except Exception as e:
            logger.error(f"Failed to get file info for {url}: {e}")
            return None
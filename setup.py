"""Setup configuration for telegram-agentic-publisher."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telegram-agentic-publisher",
    version="1.0.0",
    author="Serge Bulaev",
    author_email="serge@bulaev.net",
    description="Open source Telegram poster via authorized user to any Telegram channel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sergebulaev/telegram-agentic-publisher",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "telethon>=1.34.0",
        "cryptography>=41.0.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0",
        "beautifulsoup4>=4.12.0",
        "Pillow>=10.0.0",
        "colorama>=0.4.6",
        "asyncio>=3.4.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=7.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "telegram-publisher=telegram_agentic_publisher.cli:main",
        ],
    },
)
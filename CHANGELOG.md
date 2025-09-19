# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-18

### Added
- Initial release of Telegram Agentic Publisher
- Core publishing functionality via user accounts
- Full markdown formatting support
- Media galleries (up to 10 items)
- Template system with variables, filters, conditionals, and loops
- Encrypted session management
- Command-line interface
- Media caching and optimization
- Support for both local files and URLs
- Comprehensive documentation and examples

### Features
- **Authentication**: Secure session creation and management
- **Publishing**: Post text, media, and galleries to any Telegram channel
- **Templates**: Dynamic content generation with powerful templating
- **Formatting**: Full Telegram markdown support with entity conversion
- **Media**: Smart media handling with caching and optimization
- **CLI**: Complete command-line interface for all operations
- **Security**: Encrypted session storage with optional encryption keys

### Technical
- Built with Telethon for reliable Telegram API interaction
- Asynchronous architecture for performance
- Modular design for easy extension
- Comprehensive error handling and logging
- Python 3.8+ support

## [Unreleased]

### Planned
- Scheduled posting support
- Multiple account management UI
- Web interface
- Docker support
- Webhook integration
- Analytics and reporting
- Bulk posting from CSV/JSON
- Auto-retry with exponential backoff
- Rate limiting management
- Plugin system for extensions
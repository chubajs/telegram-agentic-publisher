"""Tests for template processor."""

import pytest
from telegram_agentic_publisher.core.template_processor import TemplateProcessor


class TestTemplateProcessor:
    """Test template processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TemplateProcessor()

    def test_simple_substitution(self):
        """Test simple variable substitution."""
        template = "Hello {name}!"
        data = {"name": "World"}
        result = self.processor.process(template, data)
        assert result == "Hello World!"

    def test_nested_variables(self):
        """Test nested variable access."""
        template = "User: {user.name}, Email: {user.email}"
        data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }
        result = self.processor.process(template, data)
        assert result == "User: John Doe, Email: john@example.com"

    def test_filters(self):
        """Test filter application."""
        template = "{name|upper} - {email|lower}"
        data = {
            "name": "John Doe",
            "email": "JOHN@EXAMPLE.COM"
        }
        result = self.processor.process(template, data)
        assert result == "JOHN DOE - john@example.com"

    def test_conditionals(self):
        """Test conditional blocks."""
        template = "{?has_image}Image: {image}{/has_image}{?!has_image}No image{/has_image}"

        # With image
        data = {"has_image": True, "image": "photo.jpg"}
        result = self.processor.process(template, data)
        assert result == "Image: photo.jpg"

        # Without image
        data = {"has_image": False}
        result = self.processor.process(template, data)
        assert result == "No image"

    def test_loops(self):
        """Test loop blocks."""
        template = "Items: {#items}- {.}\n{/items}"
        data = {"items": ["Apple", "Banana", "Cherry"]}
        result = self.processor.process(template, data)
        assert result == "Items: - Apple\n- Banana\n- Cherry"

    def test_loop_with_objects(self):
        """Test loops with object items."""
        template = "{#users}Name: {name}, Age: {age}\n{/users}"
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        }
        result = self.processor.process(template, data)
        assert result == "Name: Alice, Age: 30\nName: Bob, Age: 25"

    def test_missing_variables(self):
        """Test handling of missing variables."""
        template = "Hello {name}! Your email: {email}"
        data = {"name": "John"}
        result = self.processor.process(template, data)
        # Missing variables are replaced with empty string
        assert result == "Hello John! Your email:"

    def test_escape_markdown_filter(self):
        """Test markdown escaping filter."""
        template = "{text|escape_md}"
        data = {"text": "Hello *world* with _markdown_"}
        result = self.processor.process(template, data)
        # Check that special characters are escaped
        assert result == "Hello \\*world\\* with \\_markdown\\_"

    def test_truncate_filter(self):
        """Test truncate filter."""
        template = "{text|truncate:10}"
        data = {"text": "This is a very long text that should be truncated"}
        result = self.processor.process(template, data)
        assert result == "This is a ..."
        assert len(result) <= 13  # 10 chars + "..."

    def test_default_filter(self):
        """Test default filter for missing values."""
        template = "{missing|default:N/A}"
        data = {}
        result = self.processor.process(template, data)
        assert result == "N/A"

    def test_complex_template(self):
        """Test complex template with multiple features."""
        template = """
{?has_header}# {title|upper}
{/has_header}
{content}

Tags: {#tags}[{.|lower}] {/tags}

{?author}By {author.name} ({author.email|lower}){/author}
        """
        data = {
            "has_header": True,
            "title": "Test Article",
            "content": "This is the article content.",
            "tags": ["Python", "Testing", "Code"],
            "author": {
                "name": "John Doe",
                "email": "JOHN@EXAMPLE.COM"
            }
        }
        result = self.processor.process(template, data)

        assert "# TEST ARTICLE" in result
        assert "This is the article content." in result
        assert "[python]" in result
        assert "[testing]" in result
        assert "By John Doe (john@example.com)" in result
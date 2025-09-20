"""Template processing for dynamic content generation."""

import re
from typing import Dict, Any
from datetime import datetime
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class TemplateProcessor:
    """Processes templates with placeholders and logic."""

    def __init__(self):
        """Initialize template processor."""
        self.filters = {
            "upper": lambda x: str(x).upper(),
            "lower": lambda x: str(x).lower(),
            "title": lambda x: str(x).title(),
            "capitalize": lambda x: str(x).capitalize(),
            "strip": lambda x: str(x).strip(),
            "truncate": lambda x, n=50: str(x)[:int(n)] + "..." if len(str(x)) > int(n) else str(x),
            "date": lambda x, fmt="%Y-%m-%d": datetime.fromisoformat(str(x)).strftime(fmt) if x else "",
            "default": lambda x, default="": x if x else default,
            "escape_md": self._escape_markdown,
        }

    def process(self, template: str, data: Dict[str, Any]) -> str:
        """
        Process template with data.

        Args:
            template: Template string with placeholders
            data: Data dictionary for substitution

        Returns:
            Processed string

        Examples:
            Simple substitution: "Hello {name}" -> "Hello World"
            With filters: "{name|upper}" -> "WORLD"
            Conditional: "{?has_image}Image: {image_url}{/has_image}"
            Loop: "{#tags}{.} {/tags}"
        """
        if not template:
            return ""

        result = template

        # Process conditionals
        result = self._process_conditionals(result, data)

        # Process loops
        result = self._process_loops(result, data)

        # Process variables with filters
        result = self._process_variables(result, data)

        # Clean up extra whitespace
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()

    def _process_variables(self, template: str, data: Dict[str, Any]) -> str:
        """
        Process variable substitutions with optional filters.

        Args:
            template: Template string
            data: Data dictionary

        Returns:
            Processed string
        """
        def replace_var(match):
            var_expr = match.group(1)

            # Check for filters
            if "|" in var_expr:
                parts = var_expr.split("|")
                var_name = parts[0].strip()
                filter_expr = parts[1].strip()

                # Get variable value
                value = self._get_nested_value(data, var_name)

                # Parse filter and arguments
                if ":" in filter_expr:
                    filter_name, filter_args = filter_expr.split(":", 1)
                    filter_args = filter_args.strip()
                else:
                    filter_name = filter_expr
                    filter_args = None

                # Apply filter
                if filter_name in self.filters:
                    try:
                        if filter_args:
                            # Parse filter arguments
                            if filter_args.startswith('"') and filter_args.endswith('"'):
                                filter_args = filter_args[1:-1]
                            value = self.filters[filter_name](value, filter_args)
                        else:
                            value = self.filters[filter_name](value)
                    except Exception as e:
                        logger.warning(f"Failed to apply filter {filter_name}: {e}")

                return str(value) if value is not None else ""
            else:
                # Simple variable substitution
                value = self._get_nested_value(data, var_expr.strip())
                return str(value) if value is not None else ""

        # Replace variables
        pattern = r'\{([^{}]+)\}'
        return re.sub(pattern, replace_var, template)

    def _process_conditionals(self, template: str, data: Dict[str, Any]) -> str:
        """
        Process conditional blocks.

        Args:
            template: Template string
            data: Data dictionary

        Returns:
            Processed string
        """
        # Process conditionals iteratively to handle all patterns
        result = template
        while True:
            # Pattern for conditional blocks {?condition}...{/condition}
            # Match the closing tag more flexibly
            pattern = r'\{\?(\!?[^}]+)\}(.*?)\{/[^}]+\}'

            match = re.search(pattern, result, flags=re.DOTALL)
            if not match:
                break

            condition = match.group(1).strip()
            content = match.group(2)

            # Check if condition is negated
            if condition.startswith("!"):
                base_condition = condition[1:]
                negate = True
            else:
                base_condition = condition
                negate = False

            # Evaluate condition
            value = self._get_nested_value(data, base_condition)
            is_true = bool(value)

            if negate:
                is_true = not is_true

            replacement = content if is_true else ""
            result = result[:match.start()] + replacement + result[match.end():]

        return result

    def _process_loops(self, template: str, data: Dict[str, Any]) -> str:
        """
        Process loop blocks.

        Args:
            template: Template string
            data: Data dictionary

        Returns:
            Processed string
        """
        # Pattern for loop blocks {#items}...{/items}
        pattern = r'\{#([^}]+)\}(.*?)\{/\1\}'

        def replace_loop(match):
            loop_var = match.group(1).strip()
            loop_content = match.group(2)

            # Get list value
            items = self._get_nested_value(data, loop_var)
            if not isinstance(items, (list, tuple)):
                return ""

            result = []
            for i, item in enumerate(items):
                # Create context for loop iteration
                loop_data = data.copy()
                loop_data["."] = item  # Current item
                loop_data["index"] = i  # Current index
                loop_data["first"] = i == 0
                loop_data["last"] = i == len(items) - 1

                # If item is a dict, merge it with loop data
                if isinstance(item, dict):
                    loop_data.update(item)

                # Process loop content with loop context
                processed = self._process_variables(loop_content, loop_data)
                result.append(processed)

            return "".join(result)

        return re.sub(pattern, replace_loop, template, flags=re.DOTALL)

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.

        Args:
            data: Data dictionary
            path: Dot-separated path (e.g., "user.name")

        Returns:
            Value at path or None
        """
        if not path or not data:
            return None

        # Handle special current item reference
        if path == ".":
            return data.get(".", None)

        parts = path.split(".")
        current: Any = data

        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None

        return current

    def _escape_markdown(self, text: str) -> str:
        """
        Escape special markdown characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        special_chars = ['*', '_', '~', '`', '[', ']', '(', ')', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        result = str(text)
        for char in special_chars:
            result = result.replace(char, f'\\{char}')
        return result

    def add_filter(self, name: str, func):
        """
        Add custom filter function.

        Args:
            name: Filter name
            func: Filter function
        """
        self.filters[name] = func

    def remove_filter(self, name: str):
        """
        Remove filter function.

        Args:
            name: Filter name
        """
        if name in self.filters:
            del self.filters[name]

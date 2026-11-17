"""Extract Python dicts from HTML, XML and JSON using declarative configs."""

from .json_parser import JsonParser
from .page_parser import ItemExtractor, PageParser

__version__ = "2.0.0"
__all__ = ["ItemExtractor", "JsonParser", "PageParser", "__version__"]

# Kept for backwards compatibility.
name = "parse_utils"

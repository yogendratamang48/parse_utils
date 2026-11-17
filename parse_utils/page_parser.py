"""Extract dictionaries from HTML/XML documents using XPath configs."""

from __future__ import annotations

import copy
import re
import warnings
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Union

from lxml import etree, html

__all__ = ["FieldSpec", "ItemExtractor", "PageParser"]

#: A field is one XPath, a list of fallback XPaths, or a dict with options:
#: ``{"xpath": str | list[str], "format": "text" | "markdown"}``.
FieldSpec = Union[str, Sequence[str], Mapping[str, Any]]

_FORMATS = ("text", "markdown")
_FIELD_KEYS = {"xpath", "format"}
_XML_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>")

# Elements that start a new line when ``linebreaks=True``.
_BLOCK_TAGS = frozenset(
    "address article aside blockquote dd div dl dt fieldset figcaption figure "  # noqa: SIM905
    "footer form h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre section "
    "table tbody td tfoot th thead tr ul".split()
)


def _strip_xml_declaration(content: str | bytes) -> str | bytes:
    # lxml refuses `str` input that carries an encoding declaration. A `str`
    # is already decoded, so the declaration carries no information.
    if isinstance(content, str):
        return _XML_DECLARATION.sub("", content, count=1)
    return content


def _local_name(element: etree._Element) -> str | None:
    if not isinstance(element.tag, str):  # comments, processing instructions
        return None
    return etree.QName(element).localname.lower()


def _element_text(element: etree._Element, linebreaks: bool = False) -> str:
    if not linebreaks:
        text = etree.tostring(element, method="text", encoding="unicode", with_tail=False)
        return text.strip()

    element = copy.deepcopy(element)
    for node in element.iter():
        name = _local_name(node)
        if name == "br":
            node.tail = "\n" + (node.tail or "")
        elif name in _BLOCK_TAGS:
            node.text = "\n" + (node.text or "")
            node.tail = "\n" + (node.tail or "")
    text = etree.tostring(element, method="text", encoding="unicode", with_tail=False)
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def _element_markdown(element: etree._Element) -> str:
    try:
        from markdownify import markdownify
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            'Markdown output requires markdownify: pip install "parse-utils[markdown]"'
        ) from exc
    source = etree.tostring(element, encoding="unicode", with_tail=False)
    return str(markdownify(source)).strip()


def _parse_field_spec(key: str, spec: FieldSpec) -> tuple[list[str], str]:
    fmt = "text"
    if isinstance(spec, Mapping):
        unknown = set(spec) - _FIELD_KEYS
        if unknown:
            raise ValueError(f"Field {key!r}: unknown option(s) {sorted(unknown)}")
        if "xpath" not in spec:
            raise ValueError(f"Field {key!r}: missing 'xpath'")
        fmt = spec.get("format", "text")
        if fmt not in _FORMATS:
            raise ValueError(f"Field {key!r}: format must be one of {_FORMATS}, got {fmt!r}")
        spec = spec["xpath"]

    xpaths = [spec] if isinstance(spec, str) else list(spec)
    if not xpaths or not all(isinstance(x, str) for x in xpaths):
        raise ValueError(f"Field {key!r}: expected an XPath string or a list of them")
    return xpaths, fmt


class PageParser:
    """Wraps a parsed HTML/XML tree and extracts dicts from it via XPath.

    Build one with :meth:`from_html`, :meth:`from_xml` or :meth:`from_element`.
    ``PageParser(content)`` is equivalent to ``PageParser.from_html(content)``,
    and ``PageParser(element)`` to ``PageParser.from_element(element)``.
    """

    def __init__(self, page_content: Any, selector: bool = False) -> None:
        self._json: Any = None
        if isinstance(page_content, etree._Element):
            self.root = page_content
        elif selector:
            # Pre-2.0 behaviour: `selector=True` with a dict/list meant JSON.
            warnings.warn(
                "PageParser(data, selector=True) for JSON is deprecated; use JsonParser(data).",
                DeprecationWarning,
                stacklevel=2,
            )
            self._json = page_content
        else:
            self.root = html.fromstring(_strip_xml_declaration(page_content))

    @classmethod
    def from_html(cls, content: str | bytes) -> PageParser:
        """Parse an HTML document or fragment."""
        return cls(html.fromstring(_strip_xml_declaration(content)))

    @classmethod
    def from_xml(cls, content: str | bytes) -> PageParser:
        """Parse an XML document. Tag names keep their case; entities and
        network access are disabled."""
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        return cls(etree.fromstring(_strip_xml_declaration(content), parser))

    @classmethod
    def from_element(cls, element: etree._Element) -> PageParser:
        """Wrap an already-parsed lxml element."""
        if not isinstance(element, etree._Element):
            raise TypeError(f"Expected an lxml element, got {type(element).__name__}")
        return cls(element)

    def _values(self, xpath: str, fmt: str, linebreaks: bool) -> list[Any]:
        raw: Any = self.root.xpath(xpath)
        if not isinstance(raw, list):  # count(), string(), boolean() ...
            raw = [raw]

        values: list[Any] = []
        for value in raw:
            if isinstance(value, etree._Element):
                value = _element_markdown(value) if fmt == "markdown" else _element_text(value, linebreaks)
            elif isinstance(value, bytes):
                value = value.decode("utf-8").strip()
            elif isinstance(value, str):
                value = str(value).strip()  # drop lxml's "smart string" tree reference
            elif isinstance(value, tuple):  # namespace nodes
                value = value[1]
            if value is None or value == "":
                continue
            values.append(value)
        return values

    def extract_dict(
        self,
        config: Mapping[str, FieldSpec],
        item: Mapping[str, Any] | None = None,
        is_list: bool = False,
        linebreaks: bool = False,
    ) -> dict[str, Any]:
        """Build a dict from ``config``, which maps output keys to field specs.

        For each key the XPaths are tried in order and the first one with a
        non-empty result wins. Missing keys are left out of the result.

        Args:
            config: ``{key: FieldSpec}``.
            item: initial values; copied, not modified.
            is_list: return every match instead of the first.
            linebreaks: put block elements and ``<br>`` on separate lines when
                converting elements to text.
        """
        result = dict(item or {})
        for key, spec in config.items():
            xpaths, fmt = _parse_field_spec(key, spec)
            for xpath in xpaths:
                values = self._values(xpath, fmt, linebreaks)
                if values:
                    result[key] = values if is_list else values[0]
                    break
        return result

    def extract_items(
        self,
        results: str | Sequence[str],
        fields: Mapping[str, FieldSpec],
        *,
        item: Mapping[str, Any] | None = None,
        is_list: bool = False,
        linebreaks: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Yield one dict per row matched by ``results``.

        ``results`` is an XPath (or fallback list) selecting the rows; the
        first XPath with matches is used. ``fields`` is evaluated relative to
        each row, so use XPaths starting with ``./``. This accepts the config
        shape ``{"results": ..., "fields": ...}`` via ``extract_items(**config)``.
        """
        xpaths = [results] if isinstance(results, str) else list(results)
        rows: Any = []
        for xpath in xpaths:
            rows = self.root.xpath(xpath)
            if rows:
                break
        for row in rows:
            if not isinstance(row, etree._Element):
                raise TypeError(f"Row XPath {xpath!r} must select elements, got {type(row).__name__}")
            yield PageParser(row).extract_dict(fields, item=item, is_list=is_list, linebreaks=linebreaks)

    def extract_dict_from_json(
        self, config: Mapping[str, Any], item: Mapping[str, Any] | None = None, is_list: Any = None
    ) -> dict[str, Any]:
        """Deprecated: use :class:`parse_utils.JsonParser`."""
        from .json_parser import JsonParser

        warnings.warn(
            "extract_dict_from_json is deprecated; use JsonParser(data).extract_dict(config).",
            DeprecationWarning,
            stacklevel=2,
        )
        return JsonParser(self._json).extract_dict(config, item=item)


class ItemExtractor:
    """Deprecated: use :meth:`PageParser.extract_items`."""

    @staticmethod
    def extract_items(
        rows_xpaths: str | Sequence[str],
        config: Mapping[str, FieldSpec],
        page_content: Any,
        selector: bool = False,
        is_list: bool = False,
        item: Mapping[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        warnings.warn(
            "ItemExtractor.extract_items is deprecated; use PageParser.extract_items.",
            DeprecationWarning,
            stacklevel=2,
        )
        parser = PageParser(page_content)
        return parser.extract_items(rows_xpaths, config, item=item, is_list=is_list)

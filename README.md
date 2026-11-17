# parse-utils

Extract Python dicts from HTML, XML and JSON using small declarative configs.
You describe *where* each value lives (XPath or key path, with fallbacks) and
get back a plain `dict`.

## Installation

```bash
pip install parse-utils
pip install "parse-utils[markdown]"   # optional: HTML → Markdown output
```

Requires Python 3.9+.

## Quick start

### HTML

```python
from parse_utils import PageParser

page = PageParser.from_html("""
<html><body>
  <h1>Product</h1>
  <div class="price">$9.99</div>
  <div class="desc"><p>Small <b>and</b> light.</p></div>
</body></html>
""")

page.extract_dict({
    "title": "//h1",
    "price": ["//span[@class='price']", "//div[@class='price']/text()"],  # fallbacks
    "description": {"xpath": "//div[@class='desc']/p", "format": "markdown"},
})
# {'title': 'Product', 'price': '$9.99', 'description': 'Small **and** light.'}
```

### Repeated rows

```python
page = PageParser.from_html("""
<ul>
  <li><a href="/first">First</a><p>Item 1</p></li>
  <li><a href="/second">Second</a></li>
</ul>
""")

config = {
    "results": "//ul/li",                # XPath (or list of fallbacks) selecting rows
    "fields": {                          # evaluated relative to each row
        "title": "./a/text()",
        "link": "./a/@href",
        "description": "./p",
    },
}
list(page.extract_items(**config))
# [{'title': 'First', 'link': '/first', 'description': 'Item 1'},
#  {'title': 'Second', 'link': '/second'}]
```

### XML

`from_xml` keeps tag-name case and namespaces, and disables entity expansion
and network access.

```python
doc = PageParser.from_xml(b'<?xml version="1.0"?><Return><Name>Ann</Name></Return>')
doc.extract_dict({"name": "//Name"})   # {'name': 'Ann'}
```

### JSON

```python
from parse_utils import JsonParser

data = {"name": "Ann", "address": {"city": "Pokhara"}, "orders": [{"id": 7}], "count": 0}
JsonParser(data).extract_dict({
    "name": "name",
    "city": ["address", "city"],
    "first_order": ["orders", 0, "id"],
    "zip": [["address", "zip"], ["address", "postcode"]],  # fallbacks; neither exists
    "count": "count",
})
# {'name': 'Ann', 'city': 'Pokhara', 'first_order': 7, 'count': 0}
```

`JsonParser.from_string(text)` parses a JSON string first.

## Config reference

### HTML/XML fields (`PageParser.extract_dict`, `extract_items`)

| Spec | Meaning |
|---|---|
| `"//xpath"` | One XPath |
| `["//a", "//b"]` | Fallbacks; the first with a non-empty result wins |
| `{"xpath": ..., "format": "text" \| "markdown"}` | Same, with options. `markdown` needs the `markdown` extra |

How results are converted:

- **Elements** become their text content (descendants' text, without the element's tail), or Markdown with `format: "markdown"`.
- **Strings** (`text()`, `@attr`) are stripped. Empty strings count as no match.
- **XPath scalars** (`count()`, `boolean()`, `string()`) are returned as-is, e.g. `3.0`, `False`.

Options:

- `is_list=True` returns every match as a list instead of the first.
- `linebreaks=True` puts block elements (`p`, `div`, `li`, …) and `<br>` on separate lines.
- `item={...}` gives initial values. The dict is copied, not modified.

Keys with no match are left out of the result.

### JSON paths (`JsonParser.extract_dict`)

| Spec | Meaning |
|---|---|
| `"key"` | Top-level key |
| `["a", "b", 0]` | Path of dict keys (`str`) and list indices (`int`, negatives allowed) |
| `[["a"], ["b", 0]]` | Fallback paths |

A path that doesn't resolve (missing key, out-of-range index, stepping into a
scalar) or that resolves to `None` is skipped. Falsy values like `0`, `False`
and `[]` are kept.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check parse_utils tests
mypy parse_utils
```

See [CHANGELOG.md](CHANGELOG.md) for release notes, including the 2.0 migration guide.

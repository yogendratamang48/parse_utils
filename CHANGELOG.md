# Changelog

## 2.0.0

### Breaking changes
- Markdown output is now opt-in per field: `{"xpath": ..., "format": "markdown"}`.
  A key named `"description"` is no longer special, and the `description_format`
  argument is gone.
- `markdownify` is now an optional dependency: `pip install "parse-utils[markdown]"`.
- JSON paths no longer jump to the first list element when a string key meets a
  list. Use an explicit index: `["response", 0, "fName"]`.
- Python 3.10+ is required (3.9 is end-of-life).

### Deprecated (still work, emit `DeprecationWarning`)
- `PageParser(data, selector=True)` + `extract_dict_from_json` → `JsonParser(data).extract_dict(config)`
- `ItemExtractor.extract_items(rows, fields, content)` → `PageParser.from_html(content).extract_items(rows, fields)`
- `PageParser(element, selector=True)` → `PageParser.from_element(element)`. `PageParser(element)` also works.

### Added
- `PageParser.from_html`, `from_xml` (case-preserving, no entity expansion or network access) and `from_element`.
- `PageParser.extract_items(results, fields, ...)`, which accepts the `{"results", "fields"}` config via `**config`.
- `JsonParser`, with `from_string`.
- `linebreaks=True` now works: block elements and `<br>` go on separate lines.
- Type hints and a `py.typed` marker; `parse_utils.__version__`.
- Test suite, CI (pytest on 3.10–3.14, ruff, mypy) and a PyPI publish workflow.

### Fixed
- Markdown and text output included text that follows the selected element (its tail).
- `<form>`, `<input>`, `<select>`, `<label>` and XML elements crashed with `AttributeError`.
- XPath scalar results (`count()`, `boolean()`) crashed with `AttributeError`.
- `str` input with an XML encoding declaration raised `ValueError`.
- JSON: falsy values (`0`, `False`, `""`, `[]`) were dropped.
- JSON: a plain-string path (`"name"`) silently returned nothing.
- JSON: out-of-range indices and paths through scalars raised instead of being skipped.

### Removed
- `setup.py`, `setup.cfg` and `requirements.txt` (replaced by `pyproject.toml`), the broken no-op `PageParser.extract_items()` stub (the name is now the real method), `test.py` (replaced by `tests/`) and the IRS example.

## 1.3.5 – 1.3.6
- Packaging updates for markdownify.

## 1.3.4
- Markdown optional

## 1.3.3
- Add Markdown description

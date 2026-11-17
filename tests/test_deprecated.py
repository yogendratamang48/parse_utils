"""The pre-2.0 entry points still work but emit DeprecationWarning."""

import pytest

from parse_utils.page_parser import ItemExtractor, PageParser

ROWS = "<ul><li><a href='/1'>One</a></li><li><a href='/2'>Two</a></li></ul>"


def test_json_via_page_parser():
    with pytest.warns(DeprecationWarning):
        parser = PageParser({"a": {"b": 1}}, selector=True)
    with pytest.warns(DeprecationWarning):
        assert parser.extract_dict_from_json({"b": ["a", "b"]}) == {"b": 1}


def test_item_extractor():
    with pytest.warns(DeprecationWarning):
        items = list(ItemExtractor.extract_items("//li", {"t": "./a/text()", "l": "./a/@href"}, ROWS))
    assert items == [{"t": "One", "l": "/1"}, {"t": "Two", "l": "/2"}]

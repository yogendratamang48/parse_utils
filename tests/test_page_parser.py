import pytest
from lxml import etree, html

from parse_utils import PageParser

try:
    import markdownify  # noqa: F401

    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False

requires_markdownify = pytest.mark.skipif(not HAS_MARKDOWNIFY, reason="markdownify not installed")

HTML = """
<html>
  <head><title>Title</title></head>
  <body>
    <p id="header"><b>Header one</b></p>
    <p id="header">Header two</p>
    <p class="content">Content</p>
    <div id="desc"><p>Desc <b>bold</b></p>TAIL TEXT</div>
    <div id="lines"><p>Line one</p><p>Line <i>two</i><br>Line three</p></div>
    <form id="f"><label>Name</label><input value="x"></form>
    <a id="empty" href=""></a>
    <ul id="rows">
      <li><a href="/first"> First Item</a><p>Description 1</p></li>
      <li><a href="/second">Second Item</a><p>Description 2</p></li>
      <li><a href="/third">Third Item</a></li>
    </ul>
  </body>
</html>
"""


@pytest.fixture
def parser():
    return PageParser.from_html(HTML)


class TestExtractDict:
    def test_text_and_element(self, parser):
        config = {"header": '//p[@id="header"]', "content": ['//p[@class="content"]/text()']}
        assert parser.extract_dict(config) == {"header": "Header one", "content": "Content"}

    def test_is_list_returns_all_matches(self, parser):
        assert parser.extract_dict({"h": '//p[@id="header"]'}, is_list=True) == {
            "h": ["Header one", "Header two"]
        }

    def test_fallback_xpaths_first_non_empty_wins(self, parser):
        config = {"h": ["//nope", '//a[@id="empty"]/@href', '//p[@id="header"][2]']}
        assert parser.extract_dict(config) == {"h": "Header two"}

    def test_missing_key_is_omitted(self, parser):
        assert parser.extract_dict({"x": "//nope"}) == {}

    def test_seed_item_is_copied_not_mutated(self, parser):
        seed = {"source": "test"}
        result = parser.extract_dict({"c": '//p[@class="content"]'}, item=seed)
        assert result == {"source": "test", "c": "Content"}
        assert seed == {"source": "test"}

    def test_attribute_values_are_plain_str(self, parser):
        value = parser.extract_dict({"link": "//li[1]/a/@href"})["link"]
        assert value == "/first"
        assert type(value) is str

    def test_text_excludes_tail(self, parser):
        assert parser.extract_dict({"d": '//div[@id="desc"]/p'}) == {"d": "Desc bold"}

    def test_description_key_is_not_special(self, parser):
        # Pre-2.0 a key named "description" was converted to markdown.
        assert parser.extract_dict({"description": '//div[@id="desc"]/p'}) == {"description": "Desc bold"}

    @pytest.mark.parametrize(
        ("xpath", "expected"),
        [('//form[@id="f"]', {"v": "Name"}), ("//form/label", {"v": "Name"}), ("//input", {})],
    )
    def test_lxml_element_subclasses(self, parser, xpath, expected):
        # FormElement, LabelElement, InputElement are HtmlElement subclasses
        # and used to crash with AttributeError.
        assert parser.extract_dict({"v": xpath}) == expected

    @pytest.mark.parametrize(
        ("xpath", "expected"),
        [
            ("count(//li)", 3.0),
            ("count(//nope)", 0.0),
            ("boolean(//li)", True),
            ("boolean(//nope)", False),
            ('string(//p[@class="content"])', "Content"),
        ],
    )
    def test_xpath_scalar_results(self, parser, xpath, expected):
        assert parser.extract_dict({"v": xpath}) == {"v": expected}

    def test_empty_string_result_is_skipped(self, parser):
        assert parser.extract_dict({"v": "string(//nope)"}) == {}


class TestFormats:
    @requires_markdownify
    def test_markdown_excludes_tail(self, parser):
        config = {"d": {"xpath": '//div[@id="desc"]/p', "format": "markdown"}}
        assert parser.extract_dict(config) == {"d": "Desc **bold**"}

    @requires_markdownify
    def test_markdown_with_fallbacks(self, parser):
        config = {"d": {"xpath": ["//nope", '//div[@id="desc"]/p'], "format": "markdown"}}
        assert parser.extract_dict(config) == {"d": "Desc **bold**"}

    def test_linebreaks(self, parser):
        result = parser.extract_dict({"t": '//div[@id="lines"]'}, linebreaks=True)
        assert result == {"t": "Line one\nLine two\nLine three"}

    def test_without_linebreaks_text_is_joined(self, parser):
        assert parser.extract_dict({"t": '//div[@id="lines"]'}) == {"t": "Line oneLine twoLine three"}

    @pytest.mark.parametrize(
        "spec",
        [
            {"xpath": "//p", "format": "html"},
            {"format": "text"},
            {"xpath": "//p", "fromat": "text"},
            [],
            [1],
        ],
    )
    def test_invalid_field_spec(self, parser, spec):
        with pytest.raises(ValueError):
            parser.extract_dict({"bad": spec})


class TestExtractItems:
    FIELDS = {"title": "./a/text()", "description": ["./p"], "link": "./a/@href"}

    def test_rows(self, parser):
        items = list(parser.extract_items("//ul/li", self.FIELDS))
        assert items == [
            {"title": "First Item", "description": "Description 1", "link": "/first"},
            {"title": "Second Item", "description": "Description 2", "link": "/second"},
            {"title": "Third Item", "link": "/third"},
        ]

    def test_config_shape_and_fallback_rows(self, parser):
        config = {"results": ["//apple/ball", "//ul/li"], "fields": self.FIELDS}
        items = list(parser.extract_items(**config, item={"src": "x"}))
        assert len(items) == 3
        assert all(i["src"] == "x" for i in items)

    def test_no_rows(self, parser):
        assert list(parser.extract_items("//nope", self.FIELDS)) == []

    def test_non_element_rows_raise(self, parser):
        with pytest.raises(TypeError):
            list(parser.extract_items("//li/a/@href", self.FIELDS))


class TestConstructors:
    def test_from_xml_keeps_case_and_accepts_declaration_in_str(self):
        doc = (
            '<?xml version="1.0" encoding="utf-8"?><Return version="2"><NamePerson>Ann</NamePerson></Return>'
        )
        parser = PageParser.from_xml(doc)
        assert parser.extract_dict({"n": "//NamePerson", "v": "/Return/@version"}) == {"n": "Ann", "v": "2"}

    def test_from_xml_bytes(self):
        parser = PageParser.from_xml(b'<?xml version="1.0" encoding="utf-8"?><a><b>caf\xc3\xa9</b></a>')
        assert parser.extract_dict({"b": "//b"}) == {"b": "café"}

    def test_from_xml_does_not_expand_entities(self, tmp_path):
        secret = tmp_path / "secret.txt"
        secret.write_text("SECRET")
        doc = f'<!DOCTYPE a [<!ENTITY x SYSTEM "file://{secret}">]><a>&x;</a>'
        result = PageParser.from_xml(doc).extract_dict({"a": "/a"})
        assert "SECRET" not in result.get("a", "")

    def test_from_html_accepts_declaration_in_str(self):
        parser = PageParser.from_html('<?xml version="1.0" encoding="utf-8"?><div><p>x</p></div>')
        assert parser.extract_dict({"p": "//p"}) == {"p": "x"}

    def test_from_element_and_plain_constructor(self):
        element = html.fromstring("<div><p>x</p></div>")
        assert PageParser.from_element(element).extract_dict({"p": ".//p"}) == {"p": "x"}
        assert PageParser(element).extract_dict({"p": ".//p"}) == {"p": "x"}
        assert PageParser("<div><p>x</p></div>").extract_dict({"p": ".//p"}) == {"p": "x"}

    def test_from_element_rejects_non_elements(self):
        with pytest.raises(TypeError):
            PageParser.from_element("<p>x</p>")

    def test_xml_namespaced_elements_with_linebreaks(self):
        doc = '<r xmlns="urn:x"><p>one</p><p>two</p></r>'
        root = etree.fromstring(doc)
        assert PageParser(root).extract_dict({"r": "/*"}, linebreaks=True) == {"r": "one\ntwo"}

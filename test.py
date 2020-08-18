from parse_utils.page_parser import PageParser, ItemExtracter

html_data = """
<html>
    <head><title>This is title</title></head>
    <body>
        <p id="header">This is header id</p>
        <p id="header">This is header2</p>
        <p class="content">This is content</p>
    </body>
</html>
"""

html_rows_data = """
<html>
    <head><title>This is title</title></head>
    <body>
    <ul id="contents">
        <li><a href="/first"> First Item</a><p>Description of Item 1</p></li>
        <li><a href="/Second"> Second Item</a><p>Description of Item 2</p></li>
        <li><a href="/Second"> Second Item</a><p>Description of Item 3</p></li>
        <li><a href="/Second"> First Item</a><p>Description of Item 4</p></li>
    </ul>
        <p class="content">This is content</p>
    </body>
</html>
"""


json_data = {"name": "Yogendra", "address": {"country": "Nepal", "city": "Pokhara",}}


def test_html_parser():
    """
    """
    config = {
        "header": ['//p[@id="header"]/text()'],
        "content": ['//p[@class="content"]'],
        "body": ["//body"],
    }
    pparser = PageParser(html_data)
    item = pparser.extract_dict(config)

    item2 = pparser.extract_dict(config, is_list=True)
    print(item2["body"])
    item3 = pparser.extract_dict(config, linebreaks=True)
    print(item3["body"])
    print(item)


def test_json_parser():
    """
    """
    config = {
        "header": ["name"],
        "city": ["address", "city"],
    }
    jparser = PageParser(json_data, selector=True)
    item = jparser.extract_dict_from_json(config)
    print(item)


def test_items_parser():
    """
    """
    config = {
        "results": "//ul/li",
        "fields": {
            "title": ["./a/text()"],
            "description": ["./p"],
            "link": ["./a/@href"],
        },
    }
    for item in ItemExtracter.extract_items(
        config["results"], config["fields"], html_rows_data
    ):
        print(item)


if __name__ == "__main__":
    test_html_parser()
    test_json_parser()
    test_items_parser()

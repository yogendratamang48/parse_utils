### Parse Utilities (ParseUtils)

This package helps you extracting python dict from html/xml contents

### Installation

> `pip install parse-utils`

### Usage

```python
from parse_utils.page_parser import PageParser
html_data = '''
<html>
    <head><title>This is title</title></head>
    <body>
        <p id="header">This is header id</p>
        <p class="content">This is content</p>
    </body>
</html>
'''
config = {
    'header': ['//p[@id="header"]/text()'],
    'content': ['//p[@class="content"]'],
}
pparser = PageParser(html_data)
item = pparser.extract_dict(config)
print(item)
```

Output will be:

```bash
{'header': 'This is header id', 'content': 'This is content'}
```

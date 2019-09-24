from parse_utils.page_parser import PageParser
html_data = '''
<html>
    <head><title>This is title</title></head>
    <body>
        <p id="header">This is header id</p>
        <p id="header">This is header2</p>
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
_item = pparser.extract_dict(config, is_list=True)
print(item)
print(_item)
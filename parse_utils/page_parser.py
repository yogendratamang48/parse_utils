from lxml import html
from lxml.html import HtmlElement


class PageParser:
    def __init__(self, page_content, selector=None):
        if selector:
            self._selector = page_content
        else:
            self._selector = html.fromstring(page_content)

    def extract_items():
        """
        """

    def clean_data(self, raw, linebreaks=False):
        """
        Input:
            raw - raw html files
            linebreaks - True makes formatting 
        """
        return raw.text_content().strip()

    def extract_dict(self, config, item=None, is_list=None, linebreaks=False):
        """
        extracts attributes from selector as per in config
        """
        if not item:
            _item = dict()
        else:
            _item = {**item}
        for k, v in config.items():
            if v.__class__ != list:
                v = [v]
            for x in v:
                raw = self._selector.xpath(x)
                if not raw:
                    continue
                if raw.__class__ != list:
                    raw = [raw]

                # Building list
                for _idx, _raw in enumerate(raw):
                    if _raw.__class__ == HtmlElement:
                        _raw = self.clean_data(_raw, linebreaks=linebreaks)
                        raw[_idx] = _raw
                raw = [_.strip() for _ in raw if _.strip()]
                if raw:
                    if is_list:
                        _item[k] = raw[:]
                    else:
                        _item[k] = raw[0]
                    break
                else:
                    continue

        return _item

    def extract_dict_from_json(self, config, item=None, is_list=None):
        """
        extracts json data
        """
        if not item:
            _item = dict()
        else:
            _item = {**item}
        for _k, _pathlist in config.items():
            if _pathlist[0].__class__ != list:
                _pathlist = [_pathlist]
            for _paths in _pathlist:
                tmp = self._selector
                for _path in _paths:
                    tmp = tmp.get(_path)
                    if tmp is None:
                        break
                if tmp:
                    _item[_k] = tmp
                    break
        return _item


class ItemExtracter:
    @staticmethod
    def extract_items(rows_xpath, config, page_content, selector=None, is_list=None):
        """generator returns items
        config should have following properties
        rows_xpath: str
        config: dict
        page_content: selector or bytestring or string
        selector: based on page_content type, set to True if page_content is selector
        """
        if selector:
            _selector = page_content
        else:
            _selector = html.fromstring(page_content)
        rows = _selector.xpath(rows_xpath)
        # Use existing method
        for row in rows:
            _parser = PageParser(row, selector=True)
            item = _parser.extract_dict(config, is_list=is_list)
            yield item

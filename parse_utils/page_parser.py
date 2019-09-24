from lxml import html
from lxml.html import HtmlElement

class PageParser:
    def __init__(self, page_content, selector=None):
        if selector:
            self._selector = page_content
        else:
            self._selector = html.fromstring(page_content)
    
    def clean_data(self, raw, linebreaks=False):
        joiner = ' '
        if linebreaks:
            joiner =  '\n'
        raw = joiner.join(raw.itertext())
        raw = [r.strip() for r in raw.split() if r.strip()!='']
        return (' '.join(raw))

    def extract_dict(self, config, item=None, list=False):
        '''
        extracts attributes from selector as per in config
        '''
        if not item:
            _item = dict()
        else:
            _item = {** item }
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
                        _raw = self.clean_data(_raw)
                        raw[_idx] = _raw
                raw = [_.strip() for _ in raw if _.strip()]
                if raw:
                    if self.list:
                        _item[k] = raw[:]
                    else:
                        _item[k] = raw[0]
                    break
                else:
                    continue
               
        return _item

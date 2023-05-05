import re
from html.parser import HTMLParser

from helpers import retrieve_url
from novaprinter import prettyPrinter


class Libgen(object):
    url = 'http://libgen.is'
    name = 'Libgen'
    supported_categories = {
        'all': None,
        'fiction': 'Fiction',
        'scientific': 'Scientific',
        'technical': 'Technical',
        'scimag': 'Scientific articles',
        'comics': 'Comics',
    }

    class MyHtmlParser(HTMLParser):

        def error(self, message):
            pass

        A, TD, TR, HREF, TABLE = ('a', 'td', 'tr', 'href', 'table')

        def __init__(self, url):
            HTMLParser.__init__(self)
            self.url = url
            self.row = {}
            self.column = None
            self.insideRow = False
            self.foundTable = False
            self.foundResults = False
            self.parser_class = {
                # key: className
                'name': 'c',
                'size': 's',
                'seeds': 'se',
                'leech': 'le'
            }

        def handle_starttag(self, tag, attrs):
            params = dict(attrs)

            if 'main' in params.get('class', ''):
                self.foundResults = True
                return

            if self.foundResults and tag == self.TABLE:
                self.foundTable = True
                return

            if self.foundTable and tag == self.TR:
                self.insideRow = True
                return

            if self.insideRow and tag == self.TD:
                classList = params.get('class', None)
                for columnName, classValue in self.parser_class.items():
                    if classValue in classList:
                        self.column = columnName
                        self.row[self.column] = -1
                return

            if self.insideRow and tag == self.A:
                if self.column != 'name' or self.HREF not in params:
                    return
                link = params[self.HREF]
                if link.startswith('/book/index.php?md5='):
                    link = f'{self.url}{link}'
                    self.row['desc_link'] = link

        def handle_data(self, data):
            if self.insideRow and self.column:
                self.row[self.column] = data
                self.column = None

        def handle_endtag(self, tag):
            if tag == 'table':
                self.foundTable = False

            if self.insideRow and tag == self.TR:
                self.insideRow = False
                self.column = None
                array_length = len(self.row)
                if array_length < 1:
                    return
                prettyPrinter(self.row)
                self.row = {}

    def download_torrent(self, info):
        magnet_regex = r'magnet:\?xt=urn:btih:[a-zA-Z0-9]*'
        matches = re.findall(magnet_regex, info['desc_link'])
        if len(matches) > 0:
            print(matches[0])

    def search(self, what, cat='all'):
        category = self.supported_categories[cat]

        if category:
            page_url = f'{self.url}/search.php?req={what}&category={category}'
        else:
            page_url = f'{self.url}/search.php?req={what}'

        parser = self.MyHtmlParser(self.url)
        html = retrieve_url(page_url)
        parser.feed(html)
        parser.close()

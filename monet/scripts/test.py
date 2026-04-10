import json
import urllib.request

import urllib.parse
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List_of_paintings_by_Claude_Monet"

def fetch_page_html(title: str) -> str:
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "disabletoc": "true",
    })
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "open-museum/1.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["parse"]["text"]["*"]

html = fetch_page_html(PAGE_TITLE)
from xml.etree import ElementTree

class TableExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_th = False
        self.headers = []
        self.current_header = ""
        self.tables_headers = []
    
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.headers = []
        if tag == "th":
            self.in_th = True
            self.current_header = ""
        if tag == "tr":
            self.in_row = True
            self.current_row = []
    
    def handle_endtag(self, tag):
        if tag == "th":
            self.in_th = False
            self.headers.append(self.current_header.strip())
        if tag == "td":
            self.in_td = False
            if self.current_row is not None:
                self.current_row.append(self.current_td.strip())
            self.current_td = ""
        if tag == "tr":
            self.in_row = False
            if self.headers and not self.tables_headers:
                self.tables_headers.append(list(self.headers))
                print("HEADERS: ", self.headers)
            elif self.current_row and self.tables_headers:
                print("ROW: ", self.current_row)
            self.current_row = None
            if self.headers:
                self.headers = []
        if tag == "table" and self.headers:
            self.headers = []

    def handle_data(self, data):
        if self.in_th:
            self.current_header += data
        if self.in_td:
            self.current_td += data

ex = TableExtractor()
ex.in_td = False
ex.current_td = ""
ex.current_row = None
ex.in_row = False

def extended_starttag(self, tag, attrs):
    if tag == "table":
        self.headers = []
    if tag == "th":
        self.in_th = True
        self.current_header = ""
    if tag == "td":
        self.in_td = True
    if tag == "tr":
        self.in_row = True
        self.current_row = []

TableExtractor.handle_starttag = extended_starttag
ex.feed(html)

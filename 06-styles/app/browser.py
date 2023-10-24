import tkinter
import tkinter.font

from app.css_parser import CSSParser, style
from app.html_parser import HTMLParser, transform, tree_to_list
from app.internet import SCHEMES, request, resolve_url
from app.layout import WIDTH, HEIGHT, DocumentLayout
from app.selector import cascade_priority
from app.text import Element

STYLE_SHEET_PATH = "./files/browser.css"
SCROLL_STEP = 100
BG_COLOR = "white"


class Browser:
    def __init__(self):
        self.document = None
        self.nodes = None
        self.display_list = None
        self.scroll = 0
        with open(STYLE_SHEET_PATH) as file:
            self.default_style_sheet = CSSParser(file.read()).parse()
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg=BG_COLOR,
        )
        self.canvas.pack()

    def load(self, url):
        headers, body = request(url)
        if url.startswith(SCHEMES[4]):
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()
        rules = self.extend_rules(url)
        style(self.nodes, sorted(rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

    def extend_rules(self, url):
        rules = self.default_style_sheet.copy()
        links = [node.attributes["href"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and "href" in node.attributes
                 and node.attributes.get("rel") == "stylesheet"]
        for link in links:
            try:
                headers, body = request(resolve_url(link, url))
            except:
                continue
            rules.extend(CSSParser(body).parse())
        return rules

    # Show document on canvas.
    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def scroll_down(self, event):
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def scroll_up(self, event):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)
        self.draw()

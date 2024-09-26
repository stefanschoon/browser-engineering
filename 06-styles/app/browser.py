import tkinter
import tkinter.font

from app.css_parser import CSSParser, style
from app.html_parser import HTMLParser, transform, tree_to_list
from app.layout import WIDTH, HEIGHT, DocumentLayout
from app.selector import cascade_priority
from app.text import Element
from app.url import SCHEMES, request, resolve_url

STYLE_SHEET_PATH = "../files/browser.css"
SCROLL_STEP = 60
BG_COLOR = "white"


class Browser:
    def __init__(self):
        self.document = None
        self.nodes = None
        self.display_list = None
        self.scroll = 0
        self.height = HEIGHT
        with open(STYLE_SHEET_PATH) as file:
            self.default_style_sheet = CSSParser(file.read()).parse()
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.scroll_wheel)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg=BG_COLOR,
        )
        self.canvas.pack(fill="both", expand=1)
        self.canvas.bind("<Configure>", self.configure)

    def load(self, url):
        headers, body, view_source = request(url)
        if url.startswith(SCHEMES[4]):
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()
        rules = self.extend_rules(url)
        style(self.nodes, sorted(rules, key=cascade_priority))

    def configure(self, event):
        self.height = event.height
        self.document = DocumentLayout(self.nodes, event.width)
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
            if cmd.top > self.scroll + self.height:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def scroll_down(self, event):
        self._scroll(-SCROLL_STEP)

    def scroll_up(self, event):
        self._scroll(SCROLL_STEP)

    def scroll_wheel(self, event):
        self._scroll(event.delta)

    def resize(self, event):
        self.document.layout()
        self.display_list = self.document.display_list
        self.height = event.height
        self.draw()

    def _scroll(self, step):
        y_max = self.document.height - self.height
        if y_max > 0:
            self.scroll -= step
            if self.scroll < 0:
                self.scroll = 0
            elif self.scroll > y_max:
                self.scroll = y_max
            self.draw()
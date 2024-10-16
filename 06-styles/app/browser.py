import tkinter
import tkinter.font

from app.css_parser import CSSParser, style
from app.html_parser import HTMLParser, transform, tree_to_list
from app.layout import DocumentLayout
from app.selector import cascade_priority
from app.text import Element

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 60
STYLE_SHEET_PATH = "../files/browser.css"
BG_COLOR = "white"


def resolve_url(url, current):
    if "://" in url:
        return url
    elif url.startswith("/"):
        scheme, host_path = current.split("://", 1)
        host, old_path = host_path.split("/", 1)
        return scheme + "://" + host + url
    else:
        directory, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if directory.count("/") == 2:
                continue
            directory, _ = directory.rsplit("/", 1)
        return directory + "/" + url


class Browser:
    def __init__(self):
        self.document = None
        self.nodes = None
        self.display_list = None
        self.scroll, self.y_min, self.y_max = 0, 0, 0
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
        body = url.request()
        if url.view_source:
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()
        rules = self.extend_rules(url)
        style(self.nodes, sorted(rules, key=cascade_priority))

    def configure(self, event):
        self.height = event.height
        self.document = DocumentLayout(self.nodes, event.width)
        self.document.layout()
        self.y_max = self.document.height - self.height
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
                response_headers, body = url.request(resolve_url(link, url.url))
            except:
                continue
            rules.extend(CSSParser(body).parse())
        return rules

    # Show document on canvas.
    def draw(self):
        if self.y_max < self.scroll:
            self.scroll = self.y_max
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
        if self.y_max > self.y_min:
            self.scroll -= step
            if self.scroll < self.y_min:
                self.scroll = self.y_min
            elif self.scroll > self.y_max:
                self.scroll = self.y_max
            self.draw()

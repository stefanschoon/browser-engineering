import tkinter
import tkinter.font

from app.html_parser import HTMLParser, transform
from app.internet import SCHEMES, request
from app.layout import WIDTH, HEIGHT, DocumentLayout

SCROLL_STEP = 100


class Browser:
    def __init__(self):
        self.document = None
        self.nodes = None
        self.display_list = None
        self.scroll = 0
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack()

    def load(self, url):
        headers, body = request(url)
        if url.startswith(SCHEMES[4]):
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

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

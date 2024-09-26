import tkinter
import tkinter.font

from app.html_parser import HTMLParser, transform
from app.layout import DocumentLayout
from app.url import SCHEMES, request

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 60


class Browser:
    def __init__(self):
        self.document = None
        self.nodes = None
        self.display_list = None
        self.scroll = 0
        self.height = HEIGHT
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.scroll_wheel)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack(fill="both", expand=1)
        self.canvas.bind("<Configure>", self.configure)

    def load(self, url):
        body, view_source = request(url)
        if url.startswith(SCHEMES[4]):
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()

    def configure(self, event):
        self.height = event.height
        self.document = DocumentLayout(self.nodes, event.width)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

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

    def _scroll(self, step):
        y_min = 0
        y_max = self.document.height - self.height
        if y_max > y_min:
            self.scroll -= step
            if self.scroll < y_min:
                self.scroll = y_min
            elif self.scroll > y_max:
                self.scroll = y_max
            self.draw()

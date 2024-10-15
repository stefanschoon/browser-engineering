import tkinter
import tkinter.font

from app.html_parser import HTMLParser, transform
from app.layout import V_STEP, H_STEP, Layout

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 60
LINE_SPACE_MUL = 1.25


class Browser:
    def __init__(self):
        self.nodes = None
        self.display_list = None
        self.scroll, self.y_min, self.y_max = 0, 0, 0
        self.height = HEIGHT
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.scroll_wheel)
        self.window.bind("<MouseWheel>", self.scroll_wheel)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack(fill="both", expand=1)
        self.canvas.bind("<Configure>", self.configure)

    def load(self, url):
        body = url.request()
        if url.view_source:
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()

    def configure(self, event):
        self.height = event.height
        self.display_list = Layout(self.nodes, event.width).display_list
        self.draw()

    # Show document on canvas.
    def draw(self):
        if self.y_max < self.scroll:
            self.scroll = self.y_max
        self.canvas.delete("all")
        for x, y, c, font in self.display_list:
            # Skip characters outside the viewing window.
            if y > self.scroll + self.height:
                continue
            if y + V_STEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor="nw")

    def scroll_down(self, event):
        self._scroll(-SCROLL_STEP)

    def scroll_up(self, event):
        self._scroll(SCROLL_STEP)

    def scroll_wheel(self, event):
        self._scroll(event.delta)

    def _scroll(self, step):
        if self.y_max > self.y_min:
            self.scroll -= step
            if self.scroll < self.y_min:
                self.scroll = self.y_min
            elif self.scroll > self.y_max:
                self.scroll = self.y_max
            self.draw()

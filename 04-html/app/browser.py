import tkinter
import tkinter.font

from app.html_parser import HTMLParser, transform
from app.internet import SCHEMES, request
from app.layout import WIDTH, HEIGHT, V_STEP, H_STEP, Layout

SCROLL_STEP = 100
LINE_SPACE_MULT = 1.25


class Browser:
    def __init__(self):
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
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    # Show document on canvas.
    def draw(self):
        self.canvas.delete("all")
        for x, y, c, font in self.display_list:
            # Skip characters outside the viewing window.
            if y > self.scroll + HEIGHT:
                continue
            if y + V_STEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor="nw")

    def scroll_down(self, event):
        self.scroll += SCROLL_STEP
        self.draw()

    def scroll_up(self, event):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)
        self.draw()

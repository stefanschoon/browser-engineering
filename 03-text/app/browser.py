import tkinter
import tkinter.font

from app.text import Text, Tag
from app.layout import H_STEP, V_STEP, Layout

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 60


def lex(body, view_source):
    out = []
    text = ""
    entity = ""
    in_tag = False
    in_entity = False
    for c in body:
        if not view_source:
            if in_entity:
                entity += c
            if c == "<":
                in_tag = True
                if text:
                    out.append(Text(text))
                text = ""
            elif c == ">":
                in_tag = False
                out.append(Tag(text))
                text = ""
            else:
                if c == "&":
                    entity += c
                    in_entity = True
                elif c == ";":
                    in_entity = False
                if not in_entity:
                    if entity == "&lt;":
                        c = "<"
                    elif entity == "&gt;":
                        c = ">"
                    entity = ""
                    text += c
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))
    return out


class Browser:
    def __init__(self):
        self.tokens = None
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
            height=HEIGHT
        )
        self.canvas.pack(fill="both", expand=1)
        self.canvas.bind("<Configure>", self.configure)

    def load(self, url):
        headers, body, view_source = url.request()
        self.tokens = lex(body, view_source)

    def configure(self, event):
        self.height = event.height
        self.display_list = Layout(self.tokens, event.width).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, f in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + V_STEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=f)

    def scroll_down(self, event):
        self._scroll(-SCROLL_STEP)

    def scroll_up(self, event):
        self._scroll(SCROLL_STEP)

    def scroll_wheel(self, event):
        self._scroll(event.delta)

    def _scroll(self, step):
        y_max = self.display_list[-1][1] - self.height
        if y_max > 0:
            self.scroll -= step
            if self.scroll < 0:
                self.scroll = 0
            elif self.scroll > y_max + V_STEP:
                self.scroll = y_max + V_STEP
            self.draw()
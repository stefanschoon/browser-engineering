import tkinter
import tkinter.font

from app.text import Text

WIDTH, HEIGHT = 800, 600
H_STEP, V_STEP = 13, 18
LINE_SPACE_MULT = 1.25
FONTS = {}  # Global cache dictionary


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = H_STEP
        self.cursor_y = V_STEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        for tok in tokens:
            self.token(tok)
        self.line = []
        self.flush()

    def text(self, tok):
        font = get_font(self.size, self.weight, self.style)
        for word in tok.text.split():
            w = font.measure(word)  # Horizontal word length
            # Call flush() if end of window reached.
            if self.cursor_x + w > WIDTH - H_STEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + LINE_SPACE_MULT * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        # Set cursor_x to start of line and clear line list.
        self.cursor_x = H_STEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + LINE_SPACE_MULT * max_descent

    def token(self, tok):
        if isinstance(tok, Text):
            self.text(tok)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "/p" or tok.tag == "/h1":
            self.flush()
            self.cursor_y += V_STEP  # Little gap between paragraphs


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]

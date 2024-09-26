import tkinter
import tkinter.font

from app.draw import DrawText, DrawRect
from app.text import Text

H_STEP, V_STEP = 13, 18
LINE_SPACE_MUL = 1.25
FONTS = {}
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside", "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote", "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset", "legend", "details", "summary",
]


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text):
                continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        previous = None
        for child in self.node.children:
            if layout_mode(child) == "inline":
                proximate = InlineLayout(child, self, previous)
            else:
                proximate = BlockLayout(child, self, previous)
            self.children.append(proximate)
            previous = proximate
        for child in self.children:
            child.layout()
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        # Paint background-color.
        bg_color = self.node.style.get("background-color", "transparent")
        if bg_color != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bg_color)
            display_list.append(rect)
        for child in self.children:
            child.paint(display_list)


class InlineLayout:
    def __init__(self, node, parent, previous):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.cursor_x = None
        self.cursor_y = None
        self.weight = None
        self.style = None
        self.size = None
        self.display_list = None
        self.line = None
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        self.display_list = []
        self.cursor_x = self.x
        self.cursor_y = self.y
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        self.line = []
        self.recurse(self.node)
        self.flush("__init__")
        self.height = self.cursor_y - self.y

    def recurse(self, node):
        if isinstance(node, Text):
            self.word(node)
        else:
            if node.tag == "br":
                self.flush(node.tag)
            for child in node.children:
                self.recurse(child)

    def word(self, node):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)
        color = node.style["color"]
        font = get_font(size, weight, style)
        for word in node.text.split():
            # Call flush() if end of window reached.
            w = font.measure(word)  # Horizontal word length
            if self.cursor_x + w > self.width - H_STEP:
                self.flush()
            self.line.append((self.cursor_x, word, font, color))
            self.cursor_x += w + font.measure(" ")

    def paint(self, display_list):
        # Paint background-color below text.
        bg_color = self.node.style.get("background-color", "transparent")
        if bg_color != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bg_color)
            display_list.append(rect)
        for x, y, word, font, color in self.display_list:
            display_list.append(DrawText(x, y, word, font, color))

    def flush(self, text=None):
        if not self.line:
            #print(text)
            return

        metrics = [font.metrics() for pos_x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + LINE_SPACE_MUL * max_ascent
        for x, word, font, color in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))
        # Set cursor_x to start of line and clear line list.
        self.cursor_x = self.x
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + LINE_SPACE_MUL * max_descent


class DocumentLayout:
    def __init__(self, node, width):
        self.x = None
        self.y = None
        self.width = width
        self.height = None
        self.node = node
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width -= 2 * H_STEP
        self.x = H_STEP
        self.y = V_STEP
        child.layout()
        self.height = child.height + 2 * V_STEP

    def paint(self, display_list):
        self.children[0].paint(display_list)

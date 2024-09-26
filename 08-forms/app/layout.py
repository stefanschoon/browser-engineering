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
INPUT_WIDTH_PX = 200


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
        previous = None
        for child in self.node.children:
            if layout_mode(child) == "inline":
                proximate = InlineLayout(child, self, previous)
            else:
                proximate = BlockLayout(child, self, previous)
            self.children.append(proximate)
            previous = proximate
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        for child in self.children:
            child.layout()
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


class InlineLayout:
    def __init__(self, node, parent, previous):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.cursor_x = None
        self.previous_word = None
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
        self.new_line()
        self.recurse(self.node)
        for line in self.children:
            line.layout()
        self.height = sum([line.height for line in self.children])

    def recurse(self, node):
        if isinstance(node, Text):
            self.word(node)
        else:
            if node.tag == "br":
                self.new_line()
            elif node.tag == "input" or node.tag == "button":
                self.input(node)
            else:
                for child in node.children:
                    self.recurse(child)

    def new_line(self):
        self.previous_word = None
        self.cursor_x = self.x
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def word(self, node):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)
        font = get_font(size, weight, style)
        for word in node.text.split():
            w = font.measure(word)
            if self.cursor_x + w > self.width - H_STEP:
                self.new_line()
            line = self.children[-1]
            text = TextLayout(node, word, line, self.previous_word)
            line.children.append(text)
            self.previous_word = text
            self.cursor_x += w + font.measure(" ")

    def input(self, node):
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.x + self.width:
            self.new_line()
        line = self.children[-1]
        input = InputLayout(node, line, self.previous_word)
        line.children.append(input)
        self.previous_word = input
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)
        font = get_font(size, weight, style)
        self.cursor_x += w + font.measure(" ")

    def paint(self, display_list):
        bg_color = self.node.style.get("background-color", "transparent")
        if bg_color != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bg_color)
            display_list.append(rect)
        for child in self.children:
            child.paint(display_list)


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


class LineLayout:
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
        for word in self.children:
            word.layout()
        if not self.children:
            self.height = 0
            return
        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + LINE_SPACE_MUL * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = LINE_SPACE_MUL * (max_ascent + max_descent)

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        self.node = node
        self.word = word
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, weight, style)
        # Do not set self.y!
        self.width = self.font.measure(self.word)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")

    def paint(self, display_list):
        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, self.word, self.font, color))


class InputLayout:
    def __init__(self, node, parent, previous):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, weight, style)
        # Do not set self.y!
        self.width = INPUT_WIDTH_PX
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")

    def paint(self, display_list):
        bg_color = self.node.style.get("background-color", "transparent")
        if bg_color != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bg_color)
            display_list.append(rect)
            text = ""
            if self.node.tag == "input":
                text = self.node.attributes.get("value", "")
            elif self.node.tag == "button":
                text = self.node.children[0].text
            color = self.node.style["color"]
            display_list.append(DrawText(self.x, self.y, text, self.font, color))

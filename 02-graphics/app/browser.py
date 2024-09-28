import tkinter

WIDTH, HEIGHT = 800, 600
H_STEP, V_STEP = 13, 18
SCROLL_STEP = 60


def lex(body, view_source):
    text = ""
    entity = ""
    in_angle = False
    in_entity = False
    for c in body:
        if not view_source:
            if in_entity:
                entity += c
            if c == "<":
                in_angle = True
            elif c == ">":
                in_angle = False
            elif not in_angle:
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
    return text


def layout(text, width):
    display_list = []
    cursor_x, cursor_y = H_STEP, V_STEP
    for c in text:
        if c == "\n":
            # New paragraph
            cursor_y += 2 * V_STEP
            cursor_x = H_STEP
            continue
        cursor_x += H_STEP
        display_list.append((cursor_x, cursor_y, c))
        if cursor_x >= width - H_STEP:
            cursor_y += V_STEP
            cursor_x = H_STEP
    return display_list


class Browser:
    def __init__(self):
        self.text = None
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
            height=self.height
        )
        self.canvas.pack(fill="both", expand=1)
        self.canvas.bind("<Configure>", self.configure)

    def load(self, url):
        body = url.request()
        self.text = lex(body, url.view_source)

    def configure(self, event):
        self.height = event.height
        self.display_list = layout(self.text, event.width)
        self.draw()

    def draw(self):
        y_max = self.display_list[-1][1] - self.height
        if y_max < self.scroll:
            self.scroll = y_max + V_STEP
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + V_STEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scroll_down(self, event):
        self._scroll(-SCROLL_STEP)

    def scroll_up(self, event):
        self._scroll(SCROLL_STEP)

    def scroll_wheel(self, event):
        self._scroll(event.delta)

    def _scroll(self, step):
        y_min = 0
        y_max = self.display_list[-1][1] - self.height + V_STEP
        if y_max > y_min:
            self.scroll -= step
            if self.scroll < y_min:
                self.scroll = y_min
            elif self.scroll > y_max:
                self.scroll = y_max
            self.draw()

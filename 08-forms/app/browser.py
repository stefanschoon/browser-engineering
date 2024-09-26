import tkinter
import tkinter.font

from app.layout import get_font
from app.tab import CHROME_PX, Tab

WIDTH, HEIGHT = 800, 600
BG_COLOR, CHROME_FILL, CHROME_OUTLINE = "white", "white", "blue"
BUTTON_WIDTH, TAB_WIDTH = 40, 80
NEW_TAB_PAGE = "data:text/html,<h1>New Tab Page<h1>"


class Browser:
    ASCII = [0x20, 0x7f]

    def __init__(self):
        self.focus = None
        self.active_tab = None
        self.width = WIDTH
        self.height = HEIGHT
        self.tabs = []
        self.address_bar = ""
        self.window = tkinter.Tk()
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<MouseWheel>", self.handle_wheel)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Return>", self.handle_enter)
        self.window.bind("<BackSpace>", self.handle_backspace)
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=HEIGHT,
            bg=BG_COLOR,
        )
        self.canvas.pack(fill="both", expand=1)
        self.canvas.bind("<Configure>", self.configure)

    def load(self, url):
        self.focus = None
        self.active_tab = len(self.tabs)
        new_tab = Tab(self)
        new_tab.load(url)
        self.tabs.append(new_tab)

    # Show document on canvas.
    def configure(self, event):
        self.height = event.height
        self.width = event.width
        self.tabs[self.active_tab].render()
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.tabs[self.active_tab].draw(self.canvas)
        # Draw over halves of letter that stick out into browser chrome.
        self.canvas.create_rectangle(0, 0, self.width, CHROME_PX, fill=CHROME_FILL, outline=CHROME_OUTLINE)

        size = 18
        weight = "normal"
        style = "roman"
        tab_font = get_font(size, weight, style)

        for i, tab in enumerate(self.tabs):
            name = "Tab {}".format(i)
            x1, x2 = BUTTON_WIDTH + TAB_WIDTH * i, (BUTTON_WIDTH + TAB_WIDTH) + TAB_WIDTH * i
            self.canvas.create_line(x1, 0, x1, 40, fill=CHROME_OUTLINE)
            self.canvas.create_line(x2, 0, x2, 40, fill=CHROME_OUTLINE)
            self.canvas.create_text(x1 + 10, 10, anchor="nw", text=name, font=tab_font, fill=CHROME_OUTLINE)
            if i == self.active_tab:
                self.canvas.create_line(0, 40, x1, 40, fill=CHROME_OUTLINE)
                self.canvas.create_line(x2, 40, self.width, 40, fill=CHROME_OUTLINE)

        # New tab button:
        button_font = get_font(25, weight, style)
        self.canvas.create_rectangle(10, 10, 30, 30, outline=CHROME_OUTLINE, width=1)
        self.canvas.create_text(11, 0, anchor="nw", text="+", font=button_font, fill=CHROME_OUTLINE)

        # Address bar:
        button_font = get_font(20, weight, style)
        self.canvas.create_rectangle(40, 50, self.width - 10, 90, outline=CHROME_OUTLINE, width=1)

        # Draw the current URL or the currently-typed text:
        if self.focus == "address bar":
            self.canvas.create_text(55, 55, anchor="nw", text=self.address_bar, font=button_font, fill=CHROME_OUTLINE)
            # Draw cursor:
            w = button_font.measure(self.address_bar)
            self.canvas.create_line(55 + w, 55, 55 + w, 85, fill=CHROME_OUTLINE)
        else:
            url = self.tabs[self.active_tab].url
            self.canvas.create_text(55, 55, anchor="nw", text=url, font=button_font, fill=CHROME_OUTLINE)

        # Address bar button:
        self.canvas.create_rectangle(10, 50, 35, 90, outline=CHROME_OUTLINE, width=1)
        self.canvas.create_polygon(15, 70, 30, 55, 30, 85, fill=CHROME_OUTLINE)

    def handle_down(self, event):
        self.tabs[self.active_tab].scroll_down(event)
        self.draw()

    def handle_up(self, event):
        self.tabs[self.active_tab].scroll_up(event)
        self.draw()

    def handle_wheel(self, event):
        self.tabs[self.active_tab].scroll_wheel(event)
        self.draw()

    def handle_click(self, event):
        #print("Clicked at (" + str(event.x) + ", " + str(event.y) + ")")
        if event.y < CHROME_PX:
            self.focus = None
            if BUTTON_WIDTH <= event.x < BUTTON_WIDTH + TAB_WIDTH * len(self.tabs) and 0 <= event.y < 40:
                self.active_tab = int((event.x - BUTTON_WIDTH) / TAB_WIDTH)
            elif 10 <= event.x < 30 and 10 <= event.y < 30:
                self.load(NEW_TAB_PAGE)
                self.tabs[self.active_tab].render()
            elif 10 <= event.x < 35 and 40 <= event.y < 90:  # Clicked on back button.
                self.tabs[self.active_tab].go_back()
            elif 50 <= event.x < self.width - 10 and 40 <= event.y < 90:
                self.focus = "address bar"
                self.address_bar = ""
        else:
            self.focus = "content"
            self.tabs[self.active_tab].click(event.x, event.y - CHROME_PX)
        self.draw()

    def handle_key(self, event):
        if len(event.char) == 0:
            return
        if not (self.ASCII[0] <= ord(event.char) < self.ASCII[-1]):
            return
        if self.focus == "address bar":
            self.address_bar += event.char
            self.draw()
        elif self.focus == "content":
            self.tabs[self.active_tab].keypress(event.char)
            self.draw()

    def handle_enter(self, event):
        if self.focus == "address bar":
            self.tabs[self.active_tab].load(self.address_bar)
            self.tabs[self.active_tab].render()
            self.focus = None
            self.draw()

    def handle_backspace(self, event):
        if self.focus == "address bar":
            self.address_bar = self.address_bar[:-1]
            self.draw()

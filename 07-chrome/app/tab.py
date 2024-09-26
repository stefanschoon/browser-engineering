from app.css_parser import CSSParser, style
from app.html_parser import HTMLParser, transform, tree_to_list, print_tree
from app.layout import DocumentLayout
from app.selector import cascade_priority
from app.text import Text, Element
from app.url import SCHEMES, request, resolve_url

SCROLL_STEP = 60
CHROME_PX = 100
STYLE_SHEET_PATH = "../files/browser.css"


class Tab:
    def __init__(self, browser):
        self.width = None
        self.height = None
        self.rules = None
        self.focus = None
        self.document = None
        self.nodes = None
        self.display_list = None
        self.browser = browser
        self.history = []
        self.url = ""
        self.scroll = 0
        with open(STYLE_SHEET_PATH) as file:
            self.default_style_sheet = CSSParser(file.read()).parse()

    def load(self, url):
        self.focus = None
        self.url = url
        headers, body, view_source = request(self.url)
        self.history.append(self.url)
        if self.url.startswith(SCHEMES[4]):
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()
        self.rules = self.extend_rules(self.url)

    def extend_rules(self, url):
        rules = self.default_style_sheet.copy()
        links = [node.attributes["href"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and "href" in node.attributes
                 and node.attributes.get("rel") == "stylesheet"]

        for link in links:
            try:
                headers, body = request(resolve_url(link, url))
            except:
                continue
            rules.extend(CSSParser(body).parse())

        return rules

    def render(self):
        self.width = self.browser.width
        self.height = self.browser.height
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)

    # Show document on canvas.
    def draw(self, canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.height - CHROME_PX:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - CHROME_PX, canvas)

    def scroll_down(self, event):
        self._scroll(-SCROLL_STEP)

    def scroll_up(self, event):
        self._scroll(SCROLL_STEP)

    def scroll_wheel(self, event):
        self._scroll(event.delta)

    def _scroll(self, step):
        y_max = self.document.height - (self.height - CHROME_PX)
        if y_max > 0:
            self.scroll -= step
            if self.scroll < 0:
                self.scroll = 0
            elif self.scroll > y_max:
                self.scroll = y_max

    def click(self, x, y):
        y += self.scroll
        # Find links and elements at click location.
        objs = [obj for obj in tree_to_list(self.document, [])
                if obj.x <= x < obj.x + obj.width
                and obj.y < y <= obj.y + obj.height]
        if not objs:
            return

        # Get url at click location and load it.
        element = objs[-1].node
        while element:
            if isinstance(element, Text):
                pass
            elif element.tag == "a" and "href" in element.attributes:
                url = resolve_url(element.attributes["href"], self.url)
                return self.load(url)
            element = element.parent

    def go_back(self):
        if len(self.history) > 1:
            #self.load(self.history[-2])
            self.history.pop()
            back = self.history.pop()
            self.load(back)

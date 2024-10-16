import urllib.parse

import dukpy

from app.css_parser import CSSParser, style
from app.html_parser import HTMLParser, transform, tree_to_list, print_tree
from app.js_context import JSContext
from app.layout import DocumentLayout
from app.selector import cascade_priority
from app.text import Text, Element
from app.url import request

STYLE_SHEET_PATH = "../files/browser.css"
SCROLL_STEP = 60
CHROME_PX = 100


def resolve_url(url, current):
    if "://" in url:
        return url
    elif url.startswith("/"):
        scheme, host_path = current.split("://", 1)
        host, old_path = host_path.split("/", 1)
        return scheme + "://" + host + url
    else:
        directory, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if directory.count("/") == 2:
                continue
            directory, _ = directory.rsplit("/", 1)
        return directory + "/" + url


class Tab:
    def __init__(self, browser):
        self.width = None
        self.height = None
        self.js = None
        self.rules = None
        self.focus = None
        self.document = None
        self.nodes = None
        self.display_list = None
        self.browser = browser
        self.history = []
        self.url = ""
        self.scroll, self.y_min, self.y_max = 0, 0, 0
        with open(STYLE_SHEET_PATH) as file:
            self.default_style_sheet = CSSParser(file.read()).parse()

    def load(self, url, request_body=None):
        self.focus = None
        self.url = url
        response_headers, body, view_source = request(self.url, request_body)
        self.history.append(self.url)
        if view_source:
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()
        self.rules = self.extend_rules(self.url)

    def add_scripts(self, nodes):
        scripts = [node.attributes["src"] for node
                   in tree_to_list(nodes, [])
                   if isinstance(node, Element)
                   and node.tag == "script"
                   and "src" in node.attributes]

        self.js = JSContext(self)
        for script in scripts:
            response_header, body, view_source = request(resolve_url(script, self.url))
            print("Script returned: ", dukpy.evaljs(body))
            try:
                self.js.run(body)
            except dukpy.JSRuntimeError as exception:
                print("Script", script, "crashed", exception)

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
                response_headers, body = request(resolve_url(link, url))
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
        self.y_max = self.document.height - (self.height - CHROME_PX)
        self.display_list = []
        self.document.paint(self.display_list)

    # Show document on canvas.
    def draw(self, canvas):
        if self.y_max < self.scroll:
            self.scroll = self.y_max
        for cmd in self.display_list:
            if cmd.top > self.scroll + self.height - CHROME_PX:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - CHROME_PX, canvas)
        if self.focus:
            obj = [obj for obj in tree_to_list(self.document, [])
                   if obj.node == self.focus][0]
            text = self.focus.attributes.get("value", "")
            x = obj.x + obj.font.measure(text)
            y = obj.y - self.scroll + CHROME_PX
            canvas.create_line(x, y, x, y + obj.height)

    def scroll_down(self, event):
        self._scroll(-SCROLL_STEP)

    def scroll_up(self, event):
        self._scroll(SCROLL_STEP)

    def scroll_wheel(self, event):
        self._scroll(event.delta)

    def _scroll(self, step):
        if self.y_max > 0:
            self.scroll -= step
            if self.scroll < self.y_min:
                self.scroll = self.y_min
            elif self.scroll > self.y_max:
                self.scroll = self.y_max

    def click(self, x, y):
        y += self.scroll
        # Find links and elements at click location.
        objs = [obj for obj in tree_to_list(self.document, [])
                if obj.x <= x < obj.x + obj.width
                and obj.y <= y < obj.y + obj.height]
        if not objs:
            return

        # Get url at click location and load it.
        element = objs[-1].node
        while element:
            if isinstance(element, Text):
                pass
            elif element.tag == "a" and "href" in element.attributes:
                if self.js.dispatch_event("click", element): return
                url = resolve_url(element.attributes["href"], self.url)
                return self.load(url)
            elif element.tag == "input":
                if self.js.dispatch_event("click", element): return
                self.focus = element  # Set focus on clicked element.
                element.attributes["value"] = ""
                return self.render()
            elif element.tag == "button":
                if self.js.dispatch_event("click", element): return
                while element:
                    if element.tag == "form" and "action" in element.attributes:
                        return self.submit_form(element)
                    element = element.parent
            element = element.parent

    def submit_form(self, element):
        if self.js.dispatch_event("submit", element): return
        inputs = [node for node in tree_to_list(element, [])
                  if isinstance(node, Element)
                  and node.tag == "input"
                  and "name" in node.attributes]

        request_body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            value = urllib.parse.quote(value)
            request_body += "&" + name + "=" + value
        request_body = request_body[1:]

        url = resolve_url(element.attributes["action"], self.url)
        self.load(url, request_body)

    def keypress(self, char):
        if self.focus:
            if self.js.dispatch_event("keydown", self.focus): return
            self.focus.attributes["value"] += char
            self.render()

    def go_back(self):
        if len(self.history) > 1:
            #self.load(self.history[-2])
            self.history.pop()
            back = self.history.pop()
            self.load(back)

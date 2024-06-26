import urllib.parse

import dukpy

from app.css_parser import CSSParser, style
from app.html_parser import HTMLParser, transform, tree_to_list, print_tree
from app.internet import SCHEMES, request, resolve_url, url_origin
from app.js_context import JSContext
from app.layout import HEIGHT, DocumentLayout
from app.selector import cascade_priority
from app.text import Text, Element

STYLE_SHEET_PATH = "../files/browser.css"
SCROLL_STEP = 100
CHROME_PX = 100


class Tab:
    def __init__(self):
        self.history = []
        self.url = ""
        self.scroll = 0

        with open(STYLE_SHEET_PATH) as file:
            self.default_style_sheet = CSSParser(file.read()).parse()

        self.display_list = None
        self.document = None
        self.nodes = None
        self.focus = None
        self.rules = None
        self.js = None
        self.allowed_origins = None

    def load(self, url, request_body=None):
        headers, body = request(url, self.url, request_body)
        self.focus = None
        self.url = url  # Top level url
        self.history.append(url)

        if url.startswith(SCHEMES[4]):
            self.nodes = HTMLParser(transform(body)).parse()
        else:
            self.nodes = HTMLParser(body).parse()

        self.add_allowed_origins(headers)
        self.rules = self.extend_rules(url)
        self.render()

    # Support for the Content-Security-Policy header
    def add_allowed_origins(self, headers):
        self.allowed_origins = None
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"].split()
            if len(csp) > 0 and csp[0] == "default-src":
                self.allowed_origins = csp[1:]

    def allowed_request(self, url):
        return self.allowed_origins is None or \
               url_origin(url) in self.allowed_origins

    def add_scripts(self, nodes, url):
        scripts = [node.attributes["src"] for node
                   in tree_to_list(nodes, [])
                   if isinstance(node, Element)
                   and node.tag == "script"
                   and "src" in node.attributes]

        self.js = JSContext(self)
        for script in scripts:
            script_url = resolve_url(script, url)
            if not self.allowed_request(script_url):
                print("Blocked script", script, "due to CSP")
                continue
            header, body = request(script_url, url)
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
            style_url = resolve_url(link, url)
            try:
                header, body = request(style_url, url)
            except:
                continue
            rules.extend(CSSParser(body).parse())

        return rules

    def render(self):
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)

    # Show document on canvas.
    def draw(self, canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT - CHROME_PX:
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

    def scroll_down(self):
        max_y = self.document.height - (HEIGHT - CHROME_PX)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scroll_up(self):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)

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
                url = resolve_url(element.attributes["href"], self.url)
                return self.load(url)
            elif element.tag == "input":
                self.focus = element  # Set focus on clicked element.
                element.attributes["value"] = ""
                return self.render()
            elif element.tag == "button":
                while element:
                    if element.tag == "form" and "action" in element.attributes:
                        return self.submit_form(element)
                    element = element.parent

            element = element.parent

    def submit_form(self, element):
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
            self.focus.attributes["value"] += char
            self.render()

    def go_back(self):
        if len(self.history) > 1:
            #self.load(self.history[-2])
            self.history.pop()
            back = self.history.pop()
            self.load(back)

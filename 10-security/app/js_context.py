import dukpy

from app.css_parser import CSSParser
from app.html_parser import tree_to_list, HTMLParser
from app.url import request, resolve_url, url_origin

EVENT_DISPATCH_CODE = "new Node(dukpy.handle).dispatchEvent(new Event(dukpy.type))"


class JSContext:
    def __init__(self, tab):
        self.tab = tab
        self.node_to_handle = {}
        self.handle_to_node = {}

        self.interpreter = dukpy.JSInterpreter()
        self.interpreter.export_function("log", print())
        self.interpreter.export_function("querySelectorAll", self.querySelectorAll)
        self.interpreter.export_function("getAttribute", self.getAttribute)
        self.interpreter.export_function("innerHTML_set", self.innerHTML_set)
        self.interpreter.export_function("XMLHttpRequest_send", self.XMLHttpRequest_send)
        with open("./files/runtime.js") as file:
            self.interpreter.evaljs(file.read())

    def run(self, code):
        return self.interpreter.evaljs(code)

    def get_handle(self, element):
        if element not in self.node_to_handle:
            handle = len(self.node_to_handle)
            self.node_to_handle[element] = handle
            self.handle_to_node[handle] = element
        else:
            handle = self.node_to_handle[element]

        return handle

    def dispatch_event(self, type, element):
        handle = self.node_to_handle.get(element, -1)
        self.interpreter.evaljs(
            EVENT_DISPATCH_CODE, type=type, handle=handle)
        do_default = self.interpreter.evaljs(
            EVENT_DISPATCH_CODE, type=type, handle=handle)

        return not do_default

    def querySelectorAll(self, selector_text):
        selector = CSSParser(selector_text).selector()
        nodes = [node for node
                 in tree_to_list(self.tab.nodes, [])
                 if selector.matches(node)]
        return [self.get_handle(node) for node in nodes]

    def getAttribute(self, handle, attr):
        elt = self.handle_to_node[handle]
        return elt.attributes.get(attr, None)

    def innerHTML_set(self, handle, string):
        doc = HTMLParser("<html><body>" + string + "</body></html>").parse()
        new_nodes = doc.children[0].children
        element = self.handle_to_node[handle]
        element.children = new_nodes
        for child in element.children:
            child.parent = element
        self.tab.render()

    def XMLHttpRequest_send(self, method, url, body):
        full_url = resolve_url(url, self.tab.url)
        if not self.tab.allowed_request(full_url):  # Resolve relative URLs to know if they're allowed.
            raise Exception("Cross-origin XHR blocked by CSP")
        headers, out = request(full_url, self.tab.url, payload=body)
        if url_origin(full_url) != url_origin(self.tab.url):
            raise Exception("Cross-origin XHR request not allowed")
        return out

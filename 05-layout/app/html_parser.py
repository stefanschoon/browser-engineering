from app.text import Text, Element


def unescape_entities(text):
    return text.replace("&lt;", "<").replace("&gt;", ">")


def transform(body):
    return body.replace("<", "&lt;").replace(">", "&gt;")


# Pretty printer for parser tree.
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr",
    ]
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript", "link", "meta", "title", "style", "script",
    ]
    IMPLICIT_TAGS = [
        "head", "body", "/html",
    ]

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        in_tag = False
        in_body = True
        for char in self.body:
            if char == "<":
                in_tag = True
                if text and in_body:
                    self.add_text(unescape_entities(text))
                text = ""
            elif char == ">":
                in_tag = False
                if text == self.IMPLICIT_TAGS[0]:
                    in_body = False
                elif text == "/" + self.IMPLICIT_TAGS[0]:
                    in_body = True
                self.add_tag(text)
                text = ""
            else:
                text += char
        if not in_tag and text:
            self.add_text(unescape_entities(text))
        return self.finish()

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attr_val_pair in parts[1:]:
            if "=" in attr_val_pair:
                key, value = attr_val_pair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[attr_val_pair.lower()] = ""
        return tag, attributes

    def add_text(self, text):
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]  # Add a text node as a child of the last unfinished node.
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in self.IMPLICIT_TAGS:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

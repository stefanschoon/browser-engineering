class Text:
    def __init__(self, text):
        self.text = text

    def __repr__(self) -> str:
        return "Text('{}')".format(self.text)


class Tag:
    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "Tag('{}')".format(self.tag)

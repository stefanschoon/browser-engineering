def load(url):
    body, view_source = url.request()
    show(body, view_source)


# Show document on canvas.
def show(body, view_source):
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
                    print(c, end="")
        else:
            print(c, end="")

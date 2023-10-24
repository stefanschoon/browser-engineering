from app.internet import request


def load(url):
    headers, body = request(url)
    show(body)


# Show document on canvas.
def show(body):
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")

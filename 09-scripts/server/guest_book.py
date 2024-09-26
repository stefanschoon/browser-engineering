import urllib.parse

ORIGIN_PORT = 8000
CODEC = "UTF-8"
SERVER_SCRIPT_PATH = "./files/comment.js"
STYLE_SHEET_PATH = "./files/comment.css"
ENTRIES = ['Pavel was here']


def handle_connection(conx):
    request = conx.makefile("b")
    request_line = request.readline().decode(CODEC)
    method, url, version = request_line.split(" ", 2)
    assert method in ["GET", "POST"]

    # Parse request headers:
    request_headers = {}
    for line in request:
        line = line.decode(CODEC)
        if line == '\r\n':
            break
        header, value = line.split(":", 1)
        request_headers[header.lower()] = value.strip()

    if 'content-length' in request_headers:
        length = int(request_headers['content-length'])
        body = request.read(length).decode(CODEC)
    else:
        body = None

    status, body = do_request(method, url, request_headers, body)

    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Content-Length: {}\r\n".format(len(body.encode(CODEC)))
    response += "\r\n" + body
    
    conx.send(response.encode(CODEC))
    conx.close()


def do_request(method, url, request_headers, body):
    if method == "GET" and url == "/":
        return "200 OK", show_comments()
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        return "200 OK", add_entry(params)
    elif method == "GET" and url == SERVER_SCRIPT_PATH:
        with open(SERVER_SCRIPT_PATH) as file:
            return "200 OK", file.read()
    else:
        return "404 Not Found", not_found(url, method)


def form_decode(body):
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params


def show_comments():
    out = "<!doctype html>"
    out += "<form action=add method=post>"
    out += "<p><input name=guest></p>"
    out += "<p><button>Sign the book!</button></p>"
    out += "</form>"
    for entry in ENTRIES:
        out += "<p>" + entry + "</p>"
    out += "<link rel=stylesheet src=" + STYLE_SHEET_PATH
    out += "<label></label>"
    out += "<script src=" + SERVER_SCRIPT_PATH + "></script>"
    return out


def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found!</h1>".format(method, url)
    return out


def add_entry(params):
    if 'guest' in params and len(params['guest']) <= 100:
        ENTRIES.append(params['guest'])
    return show_comments()


if __name__ == "__main__":
    import socket

    soc = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    soc.bind(('', ORIGIN_PORT))
    soc.listen()
    while True:
        conx, addr = soc.accept()
        handle_connection(conx)

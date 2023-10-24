import html
import urllib.parse
import random

ORIGIN_PORT = 8000
CODEC = "UTF-8"
ENTRIES = [
    ("No names. We are nameless!", "cerealkiller"),
    ("HACK THE PLANET!!!", "crashoverride"),
]
LOGINS = {
    "crashoverride": "0cool",
    "cerealkiller": "emmanuel",
    "admin": "password",
}
SESSIONS = {}


def handle_connection(conx):
    request = conx.makefile("b")
    request_line = request.readline().decode(CODEC)
    method, url, version = request_line.split(" ", 2)
    assert method in ["GET", "POST"]

    # Parse request headers:
    headers = {}
    for line in request:
        line = line.decode(CODEC)
        if line == '\r\n':
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    if 'content-length' in headers:
        length = int(headers['content-length'])
        body = request.read(length).decode(CODEC)
    else:
        body = None

    if "cookie" in headers:
        token = headers["cookie"][len("token="):]
    else:
        token = str(random.random())[2:]

    # Assemble the HTTP response:
    session = SESSIONS.setdefault(token, {})
    status, body = do_request(session, method, url, headers, body)

    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Content-Length: {}\r\n".format(len(body.encode(CODEC)))
    if 'cookie' not in headers:
        template = "Set-Cookie: token={}; SameSite=Lax\r\n"
        response += template.format(token)
    csp = "default-src http://localhost:" + str(ORIGIN_PORT)
    response += "Content-Security-Policy: {}\r\n".format(csp)
    response += "\r\n" + body

    conx.send(response.encode(CODEC))
    conx.close()


def do_request(session, method, url, headers, body):
    if method == "GET" and url == "/":
        return "200 OK", show_comments(session)
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        return "200 OK", add_entry(session, params)
    elif method == "GET" and url == "/login":
        return "200 OK", login_form(session)
    elif method == "POST" and url == "/":
        params = form_decode(body)
        return do_login(session, params)
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


def show_comments(session):
    out = "<!doctype html>"
    if "user" in session:
        nonce = str(random.random())[2:]
        session["nonce"] = nonce
        out += "<h1>Hello, " + session["user"] + "</h1>"
        out += "<form action=add method=post>"
        out += "<p><input name=guest></p>"
        out += "<p><button>Sign the book!</button></p>"
        out += "</form>"
        out += "<input name=nonce type=hidden value=" + nonce + ">"
    else:
        out += "<a href=/login>Sign in to write in the guest book</a>"
    for entry, who in ENTRIES:
        out += "<p>" + html.escape(entry) + "\n"
        out += "<i>by " + html.escape(who) + "</i></p>"
    #out += "<script src=https://example.com/evil.js></script>"
    return out


def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found!</h1>".format(method, url)
    return out


def add_entry(session, params):
    if "nonce" not in session or "nonce" not in params:
        return
    if session["nonce"] != params["nonce"]:
        return
    if "user" not in session:
        return
    if 'guest' in params and len(params['guest']) <= 100:
        ENTRIES.append((params['guest'], session["user"]))
    return show_comments(session)


def login_form(session):
    body = "<!doctype html>"
    body += "<form action=/ method=post>"
    body += "<p>Username: <input name=username></p>"
    body += "<p>Password: <input name=password type=password></p>"
    body += "<p><button>Log in</button></p>"
    body += "</form>"
    return body


def do_login(session, params):
    username = params.get("username")
    password = params.get("password")
    if username in LOGINS and LOGINS[username] == password:
        session["user"] = username
        return "200 OK", show_comments(session)
    else:
        out = "<!doctype html>"
        out += "<h1>Invalid password for {}</h1>".format(username)
        return "401 Unauthorized", out


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

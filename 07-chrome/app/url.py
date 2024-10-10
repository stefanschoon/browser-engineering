import socket
import ssl
import gzip
from enum import Enum

CODEC = "UTF-8"
PORT_HTTP = 80
PORT_HTTPS = 443


class Scheme(Enum):
    VIEW_SOURCE = "view-source"
    ABOUT = "about"
    FILE = "file"
    DATA = "data"
    HTTP = "http"
    HTTPS = "https"

class Special(Enum):
    BLANK = "blank"


def request(url):
    view_source = False
    scheme, url = url.split(":", 1)
    scheme = scheme.lower()
    assert scheme in [scheme.value for scheme in Scheme], "Unknown scheme '{}'.".format(scheme)

    # If scheme is "view-source", split again.
    if scheme == Scheme.VIEW_SOURCE.value:
        view_source = True
        scheme, url = url.split(":", 1)
        scheme = scheme.lower()

    response_headers, body = {}, ""
    if scheme == Scheme.HTTP.value or scheme == Scheme.HTTPS.value:
        encrypted = True if scheme == Scheme.HTTPS.value else False
        url = url[2:]  # Remove the two initiating slashes.

        try:
            host, path = url.split("/", 1)
            path = "/" + path
        except ValueError:
            host = url
            path = "/"

        try:
            host, port = host.split(":", 1)
            port = int(port)
        except ValueError:
            if encrypted:
                port = PORT_HTTPS
            else:
                port = PORT_HTTP

        response_headers, body = connect(host, port, path, encrypted)
    elif scheme == Scheme.FILE.value:
        body = open_file(url[2:])  # Remove the two initiating slashes.
    elif scheme == Scheme.ABOUT.value:
        content_type, data = url.split(",", 1)
        body = handle_data(content_type, data)

    return response_headers, body, view_source


def connect(host, port, path, encrypted):
    soc = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    soc.connect((host, port))

    # Encrypted connection:
    if encrypted:
        ctx = ssl.create_default_context()
        soc = ctx.wrap_socket(soc, server_hostname=host)

    # Build request headers:
    method = "GET"
    request_headers = (
            "{} {} HTTP/1.1\r\n".format(method, path) +
            "Host: {}\r\n".format(host) +
            "Connection: close\r\n" +
            "User-Agent: haw-browser\r\n"
    )
    request_headers += "Accept-Encoding: gzip\r\n"
    request_headers += "\r\n"  # End header block with "\r\n".
    #print("Request headers:" + "\r\n" + request_headers + "\r\n")

    soc.send(request_headers.encode(CODEC))  # Encode header block.

    #response = soc.makefile("r", encoding=CODEC, newline="\r\n")
    response = soc.makefile("rb", newline="\r\n")

    status_line = response.readline().decode(CODEC)
    version, status, explanation = status_line.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    # Put response headers into map.
    response_headers = {}
    while True:
        line = response.readline().decode(CODEC)
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        # Headers are case-insensitive and whites-paces are insignificant.
        response_headers[header.lower()] = value.strip()
    #assert "transfer-encoding" not in response_headers
    #assert "content-encoding" not in response_headers
    #print("Response headers:" + "\r\n" + str(response_headers) + "\r\n")

    # Support for HTTP compression:
    if "content-encoding" in response_headers and "gzip" in response_headers["content-encoding"]:
        if "transfer-encoding" in response_headers and "chunked" in response_headers["transfer-encoding"]:
            body = read_chunks(response)
        else:
            body = response.read()
        body = gzip.decompress(body).decode(CODEC)  # Decompress body.
    else:
        body = response.read().decode(CODEC)
        #body = response.read().decode(CODEC, "ignore")

    soc.close()

    return response_headers, body


def read_chunks(response):
    body = b''
    while True:
        line = response.readline()
        chunk_length = int(line, 16)  # Chunk length is hexadecimal.

        # A chunk size of 0 is an end indication:
        if chunk_length <= 0:
            break
        elif chunk_length > 0:
            body += response.read(chunk_length)

        # Each chunk is followed by an additional empty newline (\r\n) that we have to consume.
        response.read(2)

    return body


def open_file(path):
    # Remove initiating slash if it is a Windows path.
    if path[0] == "/" and path[2] == ":":
        path = path[1:]

    file = open(path, "rt", encoding=CODEC)
    body = file.read()
    file.close()

    return body


def handle_data(content_type, data):
    return data

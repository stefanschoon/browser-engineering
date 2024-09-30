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
    DATA = " data"
    HTTP = "http"
    HTTPS = "https"

class Special(Enum):
    BLANK = "blank"

class URL:
    def __init__(self, url):
        self.host = None
        self.port = None
        self.path = None
        self.scheme, self.url = url.split(":", 1)
        self.scheme = self.scheme.lower()
        self.view_source = False
        #assert self.scheme in SCHEMES, "Unknown scheme {}".format(self.scheme)

    def request(self):
        # If scheme is "view-source", split again.
        if self.scheme == Scheme.VIEW_SOURCE:
            self.view_source = True
            self.scheme, self.url = self.url.split(":", 1)
            self.scheme = self.scheme.lower()

        response_headers, body = {}, ""
        if self.scheme == Scheme.HTTP or self.scheme == Scheme.HTTPS:
            self.url = self.url[2:]  # Remove the two initiating slashes.

            try:
                self.host, self.path = self.url.split("/", 1)
                self.path = "/" + self.path
            except ValueError:
                self.host = self.url
                self.path = "/"

            try:
                self.host, self.port = self.host.split(":", 1)
                self.port = int(self.port)
            except ValueError:
                self.port = PORT_HTTP if self.scheme == Scheme.HTTP else PORT_HTTPS

            response_headers, body = self.connect()
        elif self.scheme == Scheme.FILE:
            body = self.open_file()
        elif self.scheme == Scheme.DATA:
            content_type, data = self.url.split(",", 1)
            body = self.handle_data(content_type, data)
        elif self.scheme == Scheme.ABOUT:
            if self.url == Special.BLANK:
                pass
        else:
            # Show about:blank
            self.scheme = Scheme.ABOUT
            self.url = Special.BLANK

        return body

    def connect(self):
        soc = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        soc.connect((self.host, self.port))

        # Encrypted connection:
        if self.scheme == Scheme.HTTPS:
            ctx = ssl.create_default_context()
            soc = ctx.wrap_socket(soc, server_hostname=self.host)

        # Build request headers:
        method = "GET"
        request_headers = (
                "{} {} HTTP/1.1\r\n".format(method, self.path) +
                "Host: {}\r\n".format(self.host) +
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

        soc.close()

        return response_headers, body

    def open_file(self):
        self.url = self.url[2:]  # Remove the two initiating slashes.
        # Remove initiating slash if it is a Windows path.
        if self.url[0] == "/" and self.url[2] == ":":
            self.url = self.url[1:]

        file = open(self.url, "rt", encoding=CODEC)
        body = file.read()
        file.close()

        return body

    def handle_data(self, content_type, data):
        return data


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

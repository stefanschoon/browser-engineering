import socket
import ssl
import gzip

CODEC = "UTF-8"
SCHEMES = ["http", "https", "file", "data", "view-source", ]
PORT_HTTP = 80
PORT_HTTPS = 443


class URL:
    def __init__(self, url):
        self.scheme, self.url = url.split(":", 1)
        self.scheme = self.scheme.lower()
        assert self.scheme in SCHEMES, "Unknown scheme {}".format(self.scheme)
        self.host = None
        self.port = None
        self.path = None

    def request(self):
        view_source = False

        # If scheme is "view-source", split again.
        if self.scheme == SCHEMES[4]:
            view_source = True
            self.scheme, self.url = self.url.split(":", 1)
            self.scheme = self.scheme.lower()

        headers, body = {}, ""
        if self.scheme == SCHEMES[0] or self.scheme == SCHEMES[1]:
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
                self.port = PORT_HTTP if self.scheme == SCHEMES[0] else PORT_HTTPS

            headers, body = self.connect()
        elif self.scheme == SCHEMES[2]:
            body = self.open_file()
        elif self.scheme == SCHEMES[3]:
            content_type, data = self.url.split(",", 1)
            body = self.handle_data(content_type, data)

        return headers, body, view_source

    def connect(self):
        soc = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        soc.connect((self.host, self.port))

        # Encrypted connection:
        if self.scheme == SCHEMES[1]:
            ctx = ssl.create_default_context()
            soc = ctx.wrap_socket(soc, server_hostname=self.host)

        # Build request headers:
        method = "GET"
        req = (
                "{} {} HTTP/1.1\r\n".format(method, self.path) +
                "Host: {}\r\n".format(self.host) +
                "Connection: close\r\n" +
                "User-Agent: haw-browser\r\n"
        )
        req += "Accept-Encoding: gzip\r\n"
        req += "\r\n"  # End header block with "\r\n".
        #print("Request headers:" + "\r\n" + req + "\r\n")

        soc.send(req.encode(CODEC))  # Encode header block.

        #response = soc.makefile("r", encoding=CODEC, newline="\r\n")
        response = soc.makefile("rb", newline="\r\n")

        status_line = response.readline().decode(CODEC)
        version, status, explanation = status_line.split(" ", 2)
        assert status == "200", "{}: {}".format(status, explanation)

        # Put response headers into map.
        headers = {}
        while True:
            line = response.readline().decode(CODEC)
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            # Headers are case-insensitive and whites-paces are insignificant.
            headers[header.lower()] = value.strip()
        #assert "transfer-encoding" not in headers
        #assert "content-encoding" not in headers
        #print("Response headers:" + "\r\n" + str(headers) + "\r\n")

        # Support for HTTP compression:
        if "content-encoding" in headers and "gzip" in headers["content-encoding"]:
            if "transfer-encoding" in headers and "chunked" in headers["transfer-encoding"]:
                body = read_chunks(response)
            else:
                body = response.read()
            body = gzip.decompress(body).decode(CODEC)  # Decompress body.
        else:
            body = response.read().decode(CODEC)
            #body = response.read().decode(CODEC, "ignore")

        soc.close()

        return headers, body

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

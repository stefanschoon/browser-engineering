import socket
import ssl
import gzip

CODEC = "UTF-8"
SCHEMES = ["http", "https", "file", "data", "view-source", ]


def request(url):
    view_source = False
    scheme, url = url.split(":", 1)
    scheme = scheme.lower()
    assert scheme in SCHEMES, "Unknown scheme {}".format(scheme)

    # If scheme is "view-source", split again.
    if scheme == SCHEMES[4]:
        view_source = True
        scheme, url = url.split(":", 1)
        scheme = scheme.lower()

    headers, body = {}, ""
    if scheme == SCHEMES[0] or scheme == SCHEMES[1]:
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
            port = 80 if scheme == SCHEMES[0] else 443

        headers, body = connect(scheme, host, port, path)
    elif scheme == SCHEMES[2]:
        body = open_file(url[2:])  # Remove the two initiating slashes.
    elif scheme == SCHEMES[3]:
        content_type, data = url.split(",", 1)
        body = handle_data(content_type, data)

    return headers, body, view_source


def connect(scheme, host, port, path):
    soc = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    soc.connect((host, port))

    # Encrypted connection:
    if scheme == SCHEMES[1]:
        ctx = ssl.create_default_context()
        soc = ctx.wrap_socket(soc, server_hostname=host)

    # Build request headers:
    method = "GET"
    req = (
            "{} {} HTTP/1.1\r\n".format(method, path) +
            "Host: {}\r\n".format(host) +
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


def resolve_url(url, current):
    if "://" in url:
        return url
    elif url.startswith("/"):
        scheme, host_path = current.split("://", 1)
        host, old_path = host_path.split("/", 1)
        return scheme + "://" + host + url
    else:
        directory, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if directory.count("/") == 2:
                continue
            directory, _ = directory.rsplit("/", 1)
        return directory + "/" + url

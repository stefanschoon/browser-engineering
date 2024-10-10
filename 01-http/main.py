import sys

from app.browser import load
from app.url import URL

if __name__ == "__main__":
    #arg = sys.argv[1]
    arg = "file://../files/test.html"
    #arg = "https://example.org:443/index.html"
    #arg = "data:text/html,&lt;Hello world!&gt;"
    #arg = "view_source:file://../files/test.html"

    url = URL(arg)
    load(url)

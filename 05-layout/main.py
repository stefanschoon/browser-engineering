import sys
import tkinter

from app.browser import Browser
from app.url import URL

if __name__ == "__main__":
    #arg = sys.argv[1]
    arg = "file://../files/test.html"
    #arg = "https://example.org:443/index.html"
    #arg = "data:text/html,&lt;Hello world!&gt;"
    #arg = "view-source:https://example.org/index.html"
    #arg = "https://browser.engineering/examples/xiyouji.html"

    url = URL(arg)
    Browser().load(url)

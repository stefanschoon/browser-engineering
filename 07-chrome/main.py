import sys
import tkinter

from app.browser import Browser

if __name__ == "__main__":
    #arg = sys.argv[1]
    arg = "file://../files/test.html"
    #arg = "https://example.org:443/index.html"
    #arg = "data:text/html,&lt;Hello world!&gt;"
    #arg = "view_source:file://../files/test.html"
    #arg = "https://browser.engineering/examples/xiyouji.html"

    Browser().load(arg)

    tkinter.mainloop()

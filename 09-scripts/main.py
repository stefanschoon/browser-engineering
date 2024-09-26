import sys
import tkinter

from app.browser import Browser

if __name__ == "__main__":
    browser = Browser()
    #browser.load(sys.argv[1])
    browser.load("file://../files/test.html")
    #browser.load("http://localhost:8000/")

    tkinter.mainloop()

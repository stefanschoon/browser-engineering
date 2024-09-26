import sys
import tkinter

from app.browser import Browser

if __name__ == "__main__":
    browser = Browser()
    browser.load("file://../files/test.html")

    tkinter.mainloop()

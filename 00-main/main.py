import sys
import tkinter

from app.browser import Browser

if __name__ == "__main__":
    browser = Browser()
    browser.load("file://../files/index.html")
    tkinter.mainloop()

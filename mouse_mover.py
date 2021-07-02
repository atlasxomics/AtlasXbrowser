from tkinter import *

class MouseMover():
    def __init__(self, my_canvas):
        self.item = 0; self.previous = (0, 0); self.my_canvas = my_canvas
    def find_object(self,event):
        widget = event.widget
        tag = widget.find_closest(event.x,event.y)
        blow = widget.gettags(tag)
        self.item = blow[0]
        xc = widget.canvasx(event.x); yc = widget.canvasx(event.y)
        self.previous = (xc,yc)
    def drag(self, event):
        widget = event.widget
        xc = widget.canvasx(event.x); yc = widget.canvasx(event.y)
        self.my_canvas.move(self.item, xc-self.previous[0], yc-self.previous[1])
        self.previous = (xc, yc)
    

    


        
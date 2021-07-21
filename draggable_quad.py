import tkinter as tk
from functools import partial
import math
def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

class DrawShapes():
    def __init__(self, my_canvas):
        self.my_canvas = my_canvas
        self.points = 100, 50, 800, 50, 800, 800, 100, 800
        self.current = self.my_canvas.create_polygon(*self.points, outline="red", fill="", width=1)

    def on_click_quad(self, event):
        """fires when the user clicks on a quadrilateral ... edits the clicked on quadrilateral"""
        self.current = self.current

    def on_motion(self, event):
        """fires when the user drags the mouse ... resizes currently active quadrilateral"""
        x1, y1, x2, y2, x3, y3, x4, y4 = self.points
        ds = [distance((event.x, event.y), (x1, y1)), distance((event.x, event.y), (x2, y2)),
              distance((event.x, event.y), (x3, y3)), distance((event.x, event.y), (x4, y4))]
        dsi = ds.index(min(ds))
        if dsi == 0:
            self.points = event.x, event.y, x2, y2, x3, y3, x4, y4
        elif dsi == 1:
            self.points = x1, y1, event.x,event.y, x3,y3, x4, y4
        elif dsi == 2:
            self.points = x1, y1, x2, y2, event.x, event.y, x4, y4
        else:
            self.points = x1, y1, x2, y2, x3, y3, event.x, event.y

        self.my_canvas.coords(self.current, *self.points)




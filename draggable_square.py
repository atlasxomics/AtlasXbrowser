import tkinter as tk
from functools import partial
import math

#takes in p1 and p2 as lists of x,y coordinates for each, uses distance formula, returns result
def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

class DrawSquare():
    def __init__(self, my_canvas):
        self.my_canvas = my_canvas
        #obtaining size of canvas
        width = self.my_canvas.winfo_width()
        height = self.my_canvas.winfo_height()

        dist = distance([width*.10, height*.10], [width-(width*.10), height*.10])
        #Defining self.points as the four corners of the initial 
        self.points = width*.10, height*.10, width * .9, height*.10, width * .9, dist + height*.10, width*.10, dist + height*.10
        self.rect = [width*.10, height*.10, width-(width*.10), dist + height*.10]
        #outputting square on screen

        self.my_canvas.create_rectangle(self.rect[0],self.rect[1],self.rect[2],self.rect[3], outline="red", fill="", width=2, tag='crop')

    def on_click_quad(self, event):
        """fires when the user clicks on a quadrilateral ... edits the clicked on quadrilateral"""
        object = event.widget.find_closest(event.x,event.y)

    def on_motion(self, event):
        """fires when the user drags the mouse ... resizes currently active quadrilateral"""
        #obtaining the coordinates for all corners of the square
        x1, y1, x2, y2, x3, y3, x4, y4 = self.points
        #creating list of distances between where the mouse is and the four corners of the quad
        ds = [distance((event.x, event.y), (x1, y1)), distance((event.x, event.y), (x2, y2)),
              distance((event.x, event.y), (x3, y3)), distance((event.x, event.y), (x4, y4))]

        #taking the inx of the corner that is closeest to the spot clicked
        dsi = ds.index(min(ds))
        #Botton left corner is closest to click
        if dsi == 0:
            self.points = event.x, event.y, x2, event.y, x3, y3, event.x, y4
            self.rect = [event.x, event.y, x3, y3]
        elif dsi == 1:
            self.points = x1, event.y, event.x,event.y, event.x,y3, x4, y4
            self.rect = [x1, event.y, event.x,y3]
        elif dsi == 2:
            self.points = x1, y1, event.x, y2, event.x, event.y, x4, event.y
            self.rect = [x1, y1, event.x, event.y]
        else:
            self.points = event.x, y1, x2, y2, x3, event.y, event.x, event.y
            self.rect = [event.x, y1, x3, event.y]

        #coordinates of the square on screen changed to be the designated ones found above
        self.my_canvas.coords('crop', self.rect[0],self.rect[1],self.rect[2],self.rect[3])

    def on_release(self, event):
        #obtaining coordinates for new newly dragged quadrilateral
        coords = self.my_canvas.coords('crop')
        length1 = int(coords[2] - coords[0])
        length2 = int(coords[3] - coords[1])
        #resizing the width and height to be identical
        # the x2 coordinate is always being adjusted to make these two equal
        if length1 > length2:
            added_on = length1 - length2
            coords[3] += added_on
        if length1 < length2:
            added_on = length2 - length1
            coords[3] -= added_on
        #moving quad to be square with newly adjusted coordinates
        self.my_canvas.coords('crop', coords[0], coords[1], coords[2], coords[3])
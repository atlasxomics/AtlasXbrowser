from tkinter import *
from bsa_gui import Gui

#There is one things that need to be done in manually within the code 
#In the file tissue_grid in the first method it is shown where to update it
#When choosing a threshold value run the file thresh_value to help This is a GUI I found online
#You can use this to find a good value for the thresh. It prints to the termial the current threshvalue you are seeing
#Turn the bottom slider all the way to the LEFT ao that thresh type is Binary and the top bar is for the thresh number
#Id reccomned only clicking the ON/OFF button while the grid is showing on the picture with no channels (Show Grid)

root = Tk()
app = Gui(root)


root.mainloop()



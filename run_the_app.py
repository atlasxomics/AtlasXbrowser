import tkinter as tk
from bsa_gui import Gui
import os

#There is one things that need to be done in manually within the code 
#In the file bsa_gui in the second method (Second Window) you will see comments above code that uses the library cv2
#When choosing a threshold value run the file thresh_value to help This is a GUI I found online
#You can use this to find a good value for the thresh. It prints to the termial the current threshvalue you are seeing
#Only change the three digit number (Second value from last) when changing the adaptiveThreshold
#Id reccomned only clicking the ON/OFF button while the grid is showing on the picture with no channels (Show Grid)

root = tk.Tk()
app = Gui(root)


root.mainloop()
try:
    app.kill
    os.system('python run_the_app.py')
    os._exit(0)
except AttributeError:
    pass


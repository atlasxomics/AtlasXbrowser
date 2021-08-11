import tkinter as tk
from bsa_gui import Gui
import os

root = tk.Tk()
app = Gui(root)

root.mainloop()
try:
    app.kill
    os.system('python ABrowser.py')
    os._exit(0)
except AttributeError:
    pass


import tkinter as tk
from tkinter import ttk


class App(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self)
        self.win2_status = 0 # to open the new window once
        self.setup_frames()
        self.setup_button()

    def setup_frames(self):
        # frame for button --------------- frame 0 / button
        self.button_frame0 = ttk.LabelFrame(self, text="Azure dark Theme App", padding=(20, 10))
        self.button_frame0.grid(
            row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew")

    def setup_button(self):
        self.accentbutton = ttk.Button(
        self.button_frame0,
        text="CLick to open new window", 
        style="Accent.TButton",
        command=lambda: self.new_window(Win2)
        )
        self.accentbutton.grid(row=7, column=0, padx=5, pady=10, sticky="nsew")


    def new_window(self,winclass):
        if self.win2_status == 0:
            try:
                if self.win2.status == 'normal': # if it's not created yet
                    self.win2.focus_force()
            except:
                    self.win2 = tk.Toplevel(root) # create
                    Win2(self.win2) # populate
                    self.win2_status = 1

class Win2:
    def __init__(self, _root):
        self.root = _root
        self.root.geometry("300x300+500+200")
        self.root["bg"] = "navy"
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        print("Window destroyed")
        app.win2_status = 0
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Azure dark theme")

    # Simply set the theme
    root.tk.call("source", "azure dark/azure dark.tcl")
    style = ttk.Style(root)
    style.theme_use('azure')
    # root.tk.call("set_theme", "azure dark/images")

    app = App(root)
    app.pack(fill="both", expand=True)

    # Set a minsize for the window, and place it in the middle
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate-20))

    root.mainloop()

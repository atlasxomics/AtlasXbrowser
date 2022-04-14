import tkinter as tk
import tkinter.ttk as ttk 

root = tk.Tk()
root.geometry("400x300")
style = ttk.Style(root)
root.tk.call('source', 'azure dark/azure dark.tcl')
style.theme_use('azure')
style.configure("Accentbutton", foreground='white')
style.configure("Togglebutton", foreground='white')
button = ttk.Button(
	root,
	text="Here I am - Accent",
	style="Accentbutton")
button.pack()

var = tk.StringVar()
togglebutton = ttk.Checkbutton(
	root,
	text='Toggle button',
	style='Togglebutton',
	variable=var,
	onvalue=1)

togglebutton.pack()
var2 = tk.StringVar()
togglebutton2 = ttk.Checkbutton(
	root,
	text='Switch button',
	variable=var2,
	onvalue=1,
	style="Switch")
togglebutton2.pack()

root.mainloop()
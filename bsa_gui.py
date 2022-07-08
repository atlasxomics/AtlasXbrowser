import shutil
import tkinter as tk
from tkinter import ttk
import re
from tkinter.constants import DISABLED
from PIL import Image, ImageTk, ImageGrab
import os
import csv

from draggable_quad import DrawShapes
from draggable_square import DrawSquare
from tkinter import filedialog
from tkinter import messagebox as mb
import os
import math
import json
from tissue_grid import Tissue
import cv2
import numpy as np
import matplotlib
import matplotlib.cm
from shutil import copy, move, rmtree, copytree
from tkinter.filedialog import askopenfile, askopenfilename
Image.MAX_IMAGE_PIXELS = None
from barcode_var import barcode1_var


def center(tL,tR,bR,bL):
        top = [(tL[0]+tR[0])/2,(tL[1]+tR[1])/2]
        bottom = [(bL[0]+bR[0])/2,(bL[1]+bR[1])/2]
        x = (top[0]+bottom[0])/2
        y = (top[1]+bottom[1])/2
        return x,y
#Function for dividing line segemnt according to ratio
def ratio50l(xc,yc,xr,yr,num):
    txp = xc + (1/(num))*(xr-xc)
    typ = yc + (1/(num))*(yr-yc)
    return [txp , typ]
def from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    r, g, b = rgb
    return f'#{r:02x}{g:02x}{b:02x}'

class Gui():
    def __init__(self, root):
        self.newWindow = root
        self.screen_width = self.newWindow.winfo_screenwidth()
        self.screen_height = self.newWindow.winfo_screenheight()
        self.newWindow.title("AtlasXbrowser")
        self.newWindow.geometry("{0}x{1}".format(int(self.screen_width/1.5+290), self.screen_height))

        style = ttk.Style(root)
        root.tk.call('source', 'Azure-ttk-theme/azure/azure.tcl')
        style.theme_use('azure')

        background_image = Image.open("atlasbg.png")
        resized_image = background_image.resize((int(self.screen_width/1.5), self.screen_height), Image.ANTIALIAS)
        bg = ImageTk.PhotoImage(resized_image)

        menu = tk.Menu(self.newWindow)
        self.newWindow.config(menu=menu)
        self.filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=self.filemenu)
 
        self.filemenu.add_command(label="Begin Image Processing", command=self.load_images)
        self.filemenu.add_command(label="Open Spatial Folder", command=self.get_spatial)
        self.filemenu.add_command(label="New Instance", command=self.restart)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.destruct)
        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command="")

        self.names = []
        self.numTixels = 0
        self.excelName = None
        self.folder_selected = None
        self.topx, self.topy, self.botx, self.boty = 0, 0, 0, 0
        self.points = []
        self.Rpoints = []
        self.coords = None
        self.arr = None
        self.check_on = tk.IntVar()
        self.check_on.set(0)
        self.quad_coords = [0]
        self.rotated_degree = 0

        self.metaCreated = False

        # setting variables to be used when the default is selected
        self.barcode_filename = ""
        self.custom_barcode_selected = False
        self.custom_barcode_valid = True
        self.num_chan = 50

        self.ROILocated = False
        
        #flag to determine if user is currently in the tixel classification step
        self.classification_active = False

        #containers
        self.my_canvas = tk.Canvas(self.newWindow, width = int(self.screen_width/3), height= self.screen_height, highlightthickness = 0, bd=0)
        self.my_canvas.pack(side=tk.LEFT, anchor=tk.NW) 
        self.my_canvas.old_coords = None
        self.right_canvas = tk.Canvas(self.newWindow, width = int(self.screen_width/3) - self.screen_width, height= self.screen_height, highlightbackground="lightgray", highlightthickness=1)
        self.right_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(self.right_canvas)
        button_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.lmain = tk.Label(self.my_canvas)
        self.lmain.pack()
        self.lmain.image = bg
        self.lmain.configure(image=bg)

        #f/crop
        self.cropframe = tk.LabelFrame(self.right_canvas, text="Cropping", padx="10px", pady="10px")
        self.cropframe.place(relx=.11, rely=.01)
        self.activateCrop_button = tk.Button(self.cropframe, text = "Activate", command = self.cropping, state=tk.DISABLED)
        self.activateCrop_button.pack(side=tk.LEFT)
        self.confirmCrop_button = tk.Button(self.cropframe, text = "Confirm", command = self.square_image, state=tk.DISABLED)
        self.confirmCrop_button.pack()

        #Rotation Panel
        self.rotateframe = tk.LabelFrame(self.right_canvas, text="Rotation", padx="10px", pady="10px")
        self.rotateframe.place(relx=.11, rely=.10)
        self.image_updated = tk.Button(self.rotateframe, text = "Confirm", command = self.image_position, state=tk.DISABLED)
        self.image_updated.pack(side=tk.BOTTOM)
        rotateleft = Image.open("rotateleft.png")
        bg = ImageTk.PhotoImage(rotateleft)
        self.left = tk.Button(self.rotateframe, image=bg, command= lambda:self.image_axis(0), state=tk.DISABLED)
        self.left.image = bg
        self.left.pack(side=tk.LEFT)
        rotateright = Image.open("rotateright.png")
        bg2 = ImageTk.PhotoImage(rotateright)
        self.right = tk.Button(self.rotateframe, image=bg2, command= lambda:self.image_axis(1), state=tk.DISABLED)
        self.right.image = bg2
        self.right.pack(side=tk.LEFT)
        

        #create Scales
        self.adframe = tk.LabelFrame(self.right_canvas, text="Adaptive Thresholding", padx="10px", pady="10px")
        self.adframe.place(relx=.11, rely=.23)

        #blocksize label
        self.blockSize_label = tk.Label(self.adframe, text="blockSize", font =("Courier", 14))
        self.blockSize_label.pack(anchor='w')

        self.blockSize_value = tk.IntVar()
        self.cMean_value = tk.IntVar()
        #initializing the blockSize and cMean values
        self.blockSize_value.set(13)
        self.cMean_value.set(11)
        #blocksize scale
        self.blockSize_scale = ttk.Scale(self.adframe, variable = self.blockSize_value, from_ = 3, to = 17, orient = tk.HORIZONTAL, command= self.showThresh, length=200, state=tk.DISABLED)
        self.blockSize_scale.pack(anchor='w')
        #creating cmean labels and cmean scales
        self.cMean_label = tk.Label(self.adframe, text="C (to subtract from mean)", font =("Courier", 14))
        self.cMean_label.pack(anchor='w')
        self.cMean_scale = ttk.Scale(self.adframe, variable = self.cMean_value, from_ = 0, to = 17, orient = tk.HORIZONTAL, command= self.showThresh, length=200, state=tk.DISABLED)
        self.cMean_scale.pack(anchor='w')

        self.activateThresh_button = tk.Button(self.adframe, text="Activate", command=self.activate_thresh,
                                               state=tk.DISABLED)
        self.activateThresh_button.pack(side=tk.LEFT)
        self.confirm_thresh = tk.Button(self.adframe, text="Confirm", command=self.save_thresholded_image,
                                        state=tk.DISABLED)
        self.confirm_thresh.pack()

        #buttons
        self.thframe = tk.LabelFrame(self.right_canvas, text="Locating ROI", padx="10px", pady="10px")
        self.thframe.place(relx=.11, rely= .42)
        self.begin_button = tk.Button(self.thframe, text = "Activate", command = self.find_points, state=tk.DISABLED)
        self.begin_button.pack(side=tk.LEFT)

        self.confirm_button = tk.Button(self.thframe, text = "Confirm", command = lambda: self.confirm(None), state=tk.DISABLED)
        self.confirm_button.pack()

        self.shframe = tk.LabelFrame(self.right_canvas, text="Overlay", padx="10px", pady="10px")
        self.shframe.place(relx=.11, rely=.51)

        self.grid_button = tk.Button(self.shframe, text = "BW", command = lambda: self.grid(self.picNames[2]), state=tk.DISABLED)
        self.grid_button.pack(side=tk.LEFT)

        self.gridB_button = tk.Button(self.shframe, text = "BSA", command = lambda: self.grid(self.picNames[1]), state=tk.DISABLED)
        self.gridB_button.pack(side=tk.RIGHT)

        self.gridA_button = tk.Button(self.shframe, text = "postB", command = lambda: self.grid(self.picNames[0]), state=tk.DISABLED)
        self.gridA_button.pack(side=tk.RIGHT)

        self.labelframe = tk.LabelFrame(self.right_canvas, text="On/Off Tissue", padx="10px", pady="10px")
        self.labelframe.place(relx=.11, rely= .60)
        self.value_labelFrame = tk.IntVar()
        self.value_labelFrame.set(1)
        self.onoff_button = tk.Button(self.labelframe, text="Activate", command=lambda: self.sendinfo(self.picNames[2]),
                                      state=tk.DISABLED)
        self.onoff_button.pack(anchor='w')
        tk.Radiobutton(self.labelframe, text="Point (flip)", variable=self.value_labelFrame, value=1, command = self.offon).pack(anchor='w')
        tk.Radiobutton(self.labelframe, text="Rectangle (flip)", variable=self.value_labelFrame, value=2, command = self.highlit).pack(anchor='w')
        tk.Radiobutton(self.labelframe, text="Rectangle (all on)", variable=self.value_labelFrame, value=3,
                       command=self.highliton).pack(anchor='w')
        tk.Radiobutton(self.labelframe, text="Rectangle (all off)", variable=self.value_labelFrame, value=4,
                       command=self.highlitoff).pack(anchor='w')

        self.value_sheFrame = tk.IntVar()
        self.value_sheFrame.set(1)
        self.sheframe = tk.LabelFrame(self.right_canvas, text="Visualization", padx="10px", pady="10px",width=100)
        self.sheframe.place(relx=.11, rely= .81)
        tk.Radiobutton(self.sheframe, text="Tixel", variable=self.value_sheFrame, value=1, command= lambda:self.sendinfo(self.picNames[2])).grid(row=0,column=0)
        tk.Radiobutton(self.sheframe, text="Feature", variable=self.value_sheFrame, value=2, command= lambda: self.count(7)).grid(row=0,column=1)
        tk.Radiobutton(self.sheframe, text="Count", variable=self.value_sheFrame, value=3, command= lambda: self.count(6)).grid(row=0,column=2)

        for child in self.labelframe.winfo_children():
            if child.winfo_class() == 'Radiobutton':
                child['state'] = 'disabled'
        for child in self.sheframe.winfo_children():
            if child.winfo_class() == 'Radiobutton':
                child['state'] = 'disabled'

        self.position_file = tk.Button(self.right_canvas, text = "Create the Spatial Folder", command = self.create_files, state=tk.DISABLED)
        self.position_file.place(relx=.11, rely= .9)

        #A list to store the order in which rotations and reflections are complete
        # self.rotation_order = []

    def restart(self):
        self.newWindow.destroy()
        self.kill = True
        return self.kill
    def destruct(self):
        self.newWindow.destroy()


    def load_images(self):
        self.both_images_selected = False
        self.starting_window = tk.Toplevel(self.newWindow)
        self.starting_window.title("Selecting Images")
        self.starting_window_origwidth = 600
        self.starting_window_height = 400
        self.starting_window_width = self.starting_window_origwidth
        self.starting_window.geometry("600x400")

        x_padding = 2

        #defining a label to identify the option of selecting the BSA stained image
        label1 = tk.Label(self.starting_window, 
        text = "Select BSA image:", 
        font = ("Courier", 14),
        # width = 25
        )
        label1.grid(row = 0, column = 0, sticky = "e")

        #initializing an attibute to be modifed by get_image_file command upon button click
        self.user_selected_bsa = ""
        #button where user can select BSA
        bsa_button = tk.Button(self.starting_window, text = "File", command = lambda: self.get_image_file(0, label1a))
        bsa_button.grid(row = 0, column = 1, sticky = "w")

        #label to display the name of the selected BSA file to the user
        label1a = tk.Label(self.starting_window)
        label1a.grid(row = 0, column = 2, sticky = "w")


        label2 = tk.Label(self.starting_window, 
        text = "Select PostB image:", 
        font = ("Courier", 14),
        # width = 25,
        )
        label2.grid(row = 1, column = 0, sticky = "e")
        #label to display the name of the selected postB file to user

        label2a = tk.Label(self.starting_window)
        label2a.grid(row = 1, column =2, sticky = "w")

        #attibute to store postB image file name
        self.user_selected_postB = ""
        #button where user can select postB
        postB_button = tk.Button(self.starting_window, text = "File", command = lambda: self.get_image_file(1, label2a))
        postB_button.grid(row = 1, column = 1, sticky = "w")

        self.run_identifier = tk.StringVar()
        label3 = tk.Label(self.starting_window, 
        text = "Run ID:", 
        font = ("Courier", 14)
        # width = 25
        )

        entry_box = tk.Entry(self.starting_window, textvariable = self.run_identifier,
        )

        label3.grid(row = 2, column = 0, sticky = "e")
        entry_box.grid(row = 2, column = 1, sticky = "w")

        label5 = tk.Label(self.starting_window,
        text="Collaborator:",
        font = ("Courier", 14))
        self.collaborator = tk.StringVar()
        entry_box_collab = tk.Entry(self.starting_window, textvariable=self.collaborator)
        label5.grid(row = 3, column = 0, sticky="e")
        entry_box_collab.grid(row=3, column = 1, sticky="w")

        self.tissue = tk.StringVar()
        label4 = tk.Label(self.starting_window,
        text = "Tissue:",
        font = ("Courier", 14)
        )
        entry_box2 = tk.Entry(self.starting_window, textvariable=self.tissue)
        label4.grid(row = 4, column = 0, sticky="e")
        entry_box2.grid(row=4, column= 1, sticky="w")

        #barcode file selection
        # standard barcode 1 automatically selected. Can also designate a custom file.
        label3 = tk.Label(self.starting_window,
        text = "Barcode File:",
        font = ("Courier", 14))
        label3.grid(row = 5, column = 0, sticky = "e")

        self.barcode_selected = tk.StringVar()
        self.barcode_selected.set("1")
        barcode_options = ["1", "2", "3", "4"]
        barcode_drop = tk.OptionMenu(self.starting_window, self.barcode_selected, *barcode_options)
        barcode_drop.grid(row = 5, column = 1, sticky="w")

        self.species = tk.StringVar()
        self.species.set("Mouse")
        label6 = tk.Label(self.starting_window,
        text="Species:",
        font= ("Courier", 14))

        species_options = ["Mouse", "Human", "Rat", "Chicken"]
        species_dropdown = tk.OptionMenu(self.starting_window, self.species, *species_options)
        label6.grid(row=6, column=0, sticky="e")
        species_dropdown.grid(row=6, column=1, sticky="w")

        self.assay = tk.StringVar()
        self.assay.set("ATAC Seq")
        assay_options = ["ATAC Seq","CUT&TAG" ,"mRNA"]
        label7 = tk.Label(self.starting_window,
            text="Assay:",
            font = ("Courier", 14))
        assay_dropdown = tk.OptionMenu(self.starting_window, self.assay, *assay_options)
        label7.grid(row=7, column=0, sticky="e")
        assay_dropdown.grid(row=7, column=1, sticky="w")

        self.tissue_type = tk.StringVar()
        self.tissue_type.set("FF")
        # type_options = ["FFPE", "FF", "EFPR"]
        # label8 = tk.Label(self.starting_window,
        #                 text="Type:",
        #                 font = ("Courier", 14))
        # type_dropdown = tk.OptionMenu(self.starting_window, self.tissue_type, *type_options)
        # label8.grid(row=8, column=0, sticky="e")
        # type_dropdown.grid(row=8, column=1, sticky="w")

        self.tissue_state = tk.StringVar()
        self.tissue_state.set("Normal")
        tissue_options = ["Normal", "Disease"]
        label9 = tk.Label(self.starting_window,
                            text = "Tissue State:",
                            font = ("Courier", 14))
        tissue_state_dropdown = tk.OptionMenu(self.starting_window, self.tissue_state, *tissue_options)
        label9.grid(row=8, column = 0, sticky="e")
        tissue_state_dropdown.grid(row=8, column = 1, sticky="w")

        self.resolution = tk.StringVar()
        self.resolution.set("25")
        label10 = tk.Label(self.starting_window,
                            text = "Chip Resolution:",
                            font = ("Courier", 14))
        resolution_options = [10, 25, 50]
        resolution_dropdown = tk.OptionMenu(self.starting_window, self.resolution, *resolution_options)
        label10.grid(row=9, column = 0, sticky="e")
        resolution_dropdown.grid(row=9, column = 1, sticky="w")

        #submit button
        button = tk.Button(self.starting_window, text='Submit', font =("Courier", 14), command = lambda: self.configure_metadata())
        button.grid(row = 10, column = 1, sticky = "w", pady = 20)

        #error button
        self.error_label = tk.Label(self.starting_window)
        self.error_label.grid(row = 11, column = 1, sticky = "w")

    def use_barcode1(self, remove_button, display_button):
        self.custom_barcode_selected = False
        display_button.config(text = "bc50v1")
        remove_button.grid_remove()
        self.custom_barcode_selected = False
        self.num_chan = 50

    def get_barcode_file(self, display_button, revert_button):
        #taking file path
        file = askopenfilename()
        if file == "":
            return 

        self.custom_barcode_selected = True
        #checking if able to readlines of file
        try:
            f = open(file, "r")
            contents = f.readlines()
            total_num = len(contents)

            #taking square root of number of barcodes
            barcodes = math.sqrt(total_num)
            #ensuring this is a whole number, indicating proper barcode file
            if barcodes - int(barcodes) == 0:

                self.num_chan = int(barcodes)
                #finding name of file
                val = file.rfind("/")
                #slicing string to only be image name, not full path
                display_name = file[val + 1: ]
                #resizing popup accordingly
                self.resize_popup(display_name, display_button)
                #setting class variable
                self.barcode_filename = file
                self.custom_barcode_valid = True
                display_button.config(text = display_name)
                
        
            # if the sqrt is not a whole number, we know this is not a proper barcode file
            else:
                print("Not valid barcode")
                message = "Invalid barcode file, must include a proper number of barcodes."
                self.resize_popup(message, display_button)
                display_button.config(text = message)
                self.custom_barcode_valid = False
        
        except IsADirectoryError:
            print("This is a directory")
            msg = "Error! Cannot choose a directory."
            self.resize_popup(msg, display_button)
            display_button.config(text=msg)
            self.custom_barcode_valid = False
            

        # if not output error message on screen and ask to select text file
        except UnicodeDecodeError:
            print("Unable to open file")
            msg ="Invalid file type, must be of type .txt" 
            self.resize_popup(msg, display_button)
            display_button.config(text = msg)
            self.custom_barcode_valid = False
            
        revert_button.grid(row=2, column=2)

    #method used to resize the popup window to ensure the user is able to see the name of the file they selected
    def resize_popup(self, message, label):
        leng = len(message)
        #checking whether the length accomidated to this name is longer than current
        potential_width  = self.starting_window_origwidth + (leng * 4)
        current_width = self.starting_window.winfo_width()
        if potential_width > current_width:
            #if so the window is resized to this potential length
            self.starting_window_width = potential_width
            new_dims = str(self.starting_window_width) + "x" + str(self.starting_window_height)
            self.starting_window.geometry(new_dims)
        #adding the name of the message to the popup
        label.config(text = message)

    #method used to allow users to retrieve required image file. num is a 0 or 1 referring to whether the user is selecting a 
    #BSA or postB image respectively, and the label refers to the Label object to be updated by the name upon retrieval
    def get_image_file(self, num, label):
        #allow user to select file
        file = askopenfilename()

        #if the user selects to cancel file selection then nothing changes
        if file == "":
            return

        #flag set to false, as unsure what the user will select
        self.both_images_selected = False


        #ensuring that the selected file is an image file
        if file.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".tif")):
            #for BSA
            if num == 0:
                self.user_selected_bsa = file
                if self.user_selected_postB != "":
                    self.both_images_selected = True
                   
            #for postB
            else:
                self.user_selected_postB = file

                if self.user_selected_bsa != "":
                    self.both_images_selected = True
                        
        else:
            if num == 0:
                self.user_selected_bsa = ""
            else:
                self.user_selected_postB = ""
            file = "Error! Must select an image of type .png .jpg, .jpeg .tiff or .TIF"        

        #finding last / in the path
        val = file.rfind("/")
        #slicing string to only be image name, not full path
        display_name = file[val + 1: ]
        self.resize_popup(display_name, label)



    #method for checking whether the two photos selected by the the user are within the same folder
    def check_dirs(self, bsa_path, postB_path):
        last_back = bsa_path.rfind("/")
        bsa_folder = bsa_path[:last_back]
        
        last_back = postB_path.rfind("/")
        postB_folder = postB_path[:last_back]


        if bsa_folder == postB_folder:
            self.folder_selected = bsa_folder
            return True
        else:
            return False

    def configure_metadata(self):
        same_dir = self.check_dirs(self.user_selected_bsa, self.user_selected_postB)
        if same_dir:
            #retrieving variables from stored StringVar variables
            runID = self.run_identifier.get()
            tissue_type = self.tissue_type.get()
            collaborator = self.collaborator.get()
            resolution = self.resolution.get()
            tissue = self.tissue.get()
            print("Tissue type" + tissue_type)
            if runID != "" and collaborator != "" and tissue != "" :
                if self.both_images_selected:
                    val = self.user_selected_bsa.rfind("/")
                    self.bsa_short = self.user_selected_bsa[val + 1: ]

                    val = self.user_selected_postB.rfind("/")
                    self.postB_short = self.user_selected_postB[val + 1: ]
                    self.num_chan = 50
                    if self.barcode_selected.get() == "1":
                        self.barcode_filename = "bc50v1.txt"
                    elif self.barcode_selected.get() == "2":
                        self.barcode_filename = "bc50v2.txt"
                    elif self.barcode_selected.get() == "3":
                        self.barcode_filename = "bc50v3.txt"
                    elif self.barcode_selected.get() == "4":
                        self.barcode_filename = "bc50v4.txt" 

                    self.metadata = {
                    "run": runID,
                    "species": self.species.get(),
                    "type": self.tissue_type.get(),
                    "assay": self.assay.get(),
                    "collaborator": self.collaborator.get(),
                    "barcodes": self.barcode_selected.get(),
                    "resolution": self.resolution.get(),
                    "disease_state": self.tissue_state.get(),
                    "tissue": self.tissue.get()
                    }

                    #setting excelName var, used later, to equal the user specifed run ID
                    self.excelName = runID

                    #calling method that puts images on canvas
                    self.configure_images()

                    self.starting_window.destroy()
                    self.activateCrop_button['state'] = tk.ACTIVE
                    self.newWindow.title("AtlasXbrowser (" + runID + ")")
                    self.filemenu.entryconfig("Begin Image Processing", state = "disabled")
                    self.filemenu.entryconfig("Open Spatial Folder", state = "disabled")
                    
                else:
                    self.error_label.config(text = "Error! Must select BSA and postB Images!")
            else:
                self.error_label.config(text = "Error! Fill out necessary fields!")
        else:
         self.error_label.config(text = "Images must be located in the same directory!")
            
            

    #populates the canvas of the main page with the BSA image
    def configure_images(self):
        a = Image.open(self.user_selected_bsa)
        w, h = (a.width, a.height)
        newH = self.screen_height - 60

        self.image_array = cv2.imread(self.user_selected_bsa, 0)
        self.rotation_matrix = np.identity(len(self.image_array))

        #find ratio of 60 less than screenheight to the image height
        self.factor = newH/h
        #use ratio to calcuate the new width
        newW = int(round(w*newH/h))
        #resize the bsa image based on these calculations
        bsa = a.resize((newW, newH), Image.ANTIALIAS)
        self.qwimga = ImageTk.PhotoImage(bsa)
        #setting canvas height and width based on the size of images
        self.my_canvas.config(width = bsa.width, height= bsa.height)
        self.lmain.pack_forget()
        #loading the bsa image onto screen
        self.my_canvas.create_image(0, 0, image=self.qwimga, anchor="nw", tag ="image")
        self.newWindow.geometry("{0}x{1}".format(bsa.width + 300, self.screen_height))
        self.right_canvas.config(width = bsa.width + 300, height= h)


    #Ability to grab files from specified folder 'Spatial folder'
    def get_spatial(self):
        self.folder_selected = filedialog.askdirectory()
        
        if self.folder_selected != '':
            
            self.pWindow = tk.Toplevel(self.newWindow)
            self.pWindow.title("Loading images...")
            self.pWindow.geometry("400x90")
            self.bar = ttk.Progressbar(self.pWindow, orient="horizontal", length=360)
            self.bar.pack(pady=30)
            self.bar["value"] += 10
            self.pWindow.update_idletasks()
            self.pWindow.update()

            for file in os.listdir(self.folder_selected):
                if file.startswith(".") == False:
                     self.names.append(file)

            try:
                # self.barcode_file_spatial = open(self.folder_selected + "/barcode_file.txt")
                f = open(self.folder_selected + "/metadata.json")
                self.metadata = json.load(f)
                self.num_chan = int(self.metadata['numChannels'])
                self.numTixels = int(self.metadata['numTixels'])
                f2 = open(self.folder_selected + "/scalefactors_json.json")
                self.metadata2 = json.load(f2)
                self.tissue_hires_scalef = float(self.metadata2['tissue_hires_scalef'])
                self.bar["value"] = 20
                self.pWindow.update()
                self.second_window()
            except FileNotFoundError:
                mb.showwarning("Error", "metadata.json file is not present")
                self.pWindow.destroy()
        else:
            #Add error message
            pass
            

    #Initalize images that will be in container 
    def init_images(self):

        #opening images directly from previously stored path
        a = Image.open(self.bsa_figure_path)
        b = Image.open(self.postB_figure_path)


        w, h = (a.width, a.height)
        self.rawHeight = h
        self.width, self.height = (a.width, a.height)
        newH = self.screen_height - 60
        self.factor = newH/h

        newW = int(round(w*newH/h))
        floor = a.resize((newW, newH), Image.ANTIALIAS)
        postB = b.resize((newW, newH), Image.ANTIALIAS)

        self.refactor = b
        self.newWidth = floor.width 
        self.newHeight = floor.height 

        img = cv2.imread(self.postB_figure_path, cv2.IMREAD_UNCHANGED)

        flippedImage = img

        try:
            self.scale_image = cv2.cvtColor(flippedImage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedImage  

        self.imgA = ImageTk.PhotoImage(floor)
        self.imgB = ImageTk.PhotoImage(postB)
        self.picNames = [self.imgB, self.imgA]

        #my_canvas populated with the BSA stained image instead of the post-B image
        self.my_canvas.config(width = floor.width, height= floor.height)
        self.lmain.configure(image=self.imgA)
        self.newWindow.geometry("{0}x{1}".format(floor.width + 300, self.screen_height))
        self.right_canvas.config(width = floor.width + 300, height= h)

    #Rotate and flip the images
    def image_axis(self, num):
        (h,w) = self.cropped_image.shape[:2]
        cX, cY = (w // 2, h //2)

        if num == 0:
            M = cv2.getRotationMatrix2D((cX, cY), 90, 1.0) 
            updated = cv2.warpAffine(self.cropped_image, M, (w,h))
            I = cv2.cvtColor(updated, cv2.COLOR_BGR2RGB)
            # updated = cv2.rotate(self.cropped_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            formatted = Image.fromarray(I)
            sized = formatted.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(sized)
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            self.cropped_image = updated
            # self.rotated_degree+=-90
            self.rotated_degree += 90
            # self.rotation_order.append(90)

        if num == 1:
            M = cv2.getRotationMatrix2D((cX, cY), 270, 1.0)
            updated = cv2.warpAffine(self.cropped_image, M, (w,h))
            I = cv2.cvtColor(updated, cv2.COLOR_BGR2RGB)
            # updated = cv2.rotate(self.cropped_image, cv2.ROTATE_90_CLOCKWISE)
            formatted = Image.fromarray(I)
            sized = formatted.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(sized)
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            self.cropped_image = updated
            # self.rotated_degree+=90
            self.rotated_degree += 270
            # self.rotation_order.append(270)

    #Update postB and BSA images to new image orientation 
    def image_position(self):
        image = cv2.imread(self.bsa_figure_path)
        image1 = cv2.imread(self.postB_figure_path)
        (h,w) = image.shape[:2]

        (h1, w1) = image.shape[:2]


        cX, cY = (w // 2, h //2)
        degrees = self.rotated_degree % 360
        M = cv2.getRotationMatrix2D((cX, cY), degrees, 1.0)
        image = cv2.warpAffine(image, M, (w,h))
        image1 = cv2.warpAffine(image1, M, (w,h))

        cv2.imwrite(self.bsa_figure_path, image)
        cv2.imwrite(self.postB_figure_path, image1)

        self.metadata["orientation"] = {"rotation": degrees}

        #self.metadata["orientation"] = {"horizontal_flip": self.flipped_horz,"rotation": 90 * degree,"vertical_flip": self.flipped_vert}

        self.left['state'] = tk.DISABLED
        self.right['state'] = tk.DISABLED
        self.image_updated['state'] = tk.DISABLED
        self.activateThresh_button['state'] = tk.ACTIVE

        self.init_images()

    def cropping(self):
        #creating cropping square on screen, defined as b
        self.b = DrawSquare(self.my_canvas)
        # self.my_canvas.bind('<Button-1>', self.b.on_click_quad)
             #DOES THIS NEED TO BE INCLUDED^^^
        self.my_canvas.bind('<Button1-Motion>', self.b.on_motion)
        self.my_canvas.bind('<ButtonRelease-1>', self.b.on_release)

        #deactivating the 'activate' button, activating the 'confirm' button
   
        self.activateCrop_button['state'] = tk.DISABLED
        self.confirmCrop_button['state'] = tk.ACTIVE

    #Confirm cropping and reinitalize images in the containers
    def square_image(self):
  
        self.figure_folder = os.path.join(self.folder_selected, "figure") 
        #try making a figure folder
        try:
            os.mkdir(self.figure_folder)
        #exception if the folder already exists. If so, remove and remake
        except FileExistsError:
            rmtree(self.figure_folder)
            os.mkdir(self.figure_folder)


        #source is the source folder of the spatial images
        source = self.folder_selected
        coords = self.my_canvas.coords('crop')

        #copying the image files into the figure folder in within the same larger folder
        # for i in self.names:
        #     copy(source + "/" + i, self.figure_folder)

        copy(source + "/" + self.bsa_short, self.figure_folder)
        copy(source + "/" + self.postB_short, self.figure_folder)
            
        self.bsa_figure_path = self.figure_folder + "/" + self.bsa_short
        image1 = Image.open(self.bsa_figure_path)
        im1 = image1.crop((int(coords[0]/self.factor),int(coords[1]/self.factor),int(coords[2]/self.factor),int(coords[3]/self.factor)))
        bsa = im1.save(self.bsa_figure_path)

        self.postB_figure_path = self.figure_folder + "/" + self.postB_short
        image2 = Image.open(self.postB_figure_path)
        im2 = image2.crop((int(coords[0]/self.factor),int(coords[1]/self.factor),int(coords[2]/self.factor),int(coords[3]/self.factor))) 
        post = im2.save(self.postB_figure_path)

        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<Button1-Motion>') 

        # self.up['state'] = tk.ACTIVE
        self.left['state'] = tk.ACTIVE
        self.right['state'] = tk.ACTIVE
        # self.flip['state'] = tk.ACTIVE
        self.image_updated['state'] = tk.ACTIVE
        self.confirmCrop_button['state'] = tk.DISABLED


        b = im1

        w, h = (b.width, b.height)
        #newH is 60 less than the image height
        newH = self.screen_height - 60
        #newW is the ratio of newH to H times the width
        newW = int(round(w*newH/h))
        #creating a new image of resized BSA image base don above calculations
        floor = b.resize((newW, newH), Image.ANTIALIAS)

        #setting object height and width to the BSA images
        self.newWidth = floor.width ; self.newHeight = floor.height

        #PhotoImage of the resized BSA
        imgA = ImageTk.PhotoImage(floor)

        self.my_canvas.config(width = floor.width, height= floor.height)

        img = cv2.imread(self.bsa_figure_path, cv2.IMREAD_UNCHANGED)
        self.cropped_image = img

        self.lmain.pack()

        self.lmain.image = imgA
        self.lmain.configure(image=imgA)
        self.my_canvas.delete("image")
        self.newWindow.geometry("{0}x{1}".format(floor.width + 300, self.screen_height))
        self.right_canvas.config(width = floor.width + 300, height= h)



                        
    def activate_thresh(self):

        self.classification_active = False
        #boolean returns true if lmain does not exist
        if self.lmain.winfo_exists() == 0:
            #disable all buttons except for the "confirm"
            self.begin_button['state'] = tk.DISABLED
            self.grid_button['state'] = tk.DISABLED
            self.gridA_button['state'] = tk.DISABLED
            self.gridB_button['state'] = tk.DISABLED
            self.onoff_button['state'] = tk.DISABLED
            
            #Changing the selected radio button to display the first option of a point flip
            self.value_labelFrame.set(1)

            #removing images from the canvas
            self.my_canvas.delete("all")
            #re-creating the lmain tab which was previously destroyed
            self.lmain = tk.Label(self.my_canvas)
            self.lmain.pack()

            #ensuring the blockSize_value is odd
            numb = round(self.blockSize_value.get())
            if numb % 2 == 0:
                self.blockSize_value = tk.IntVar()
                self.blockSize_value.set(numb + 1)
        
        #disable all the satelitte buttons from that step
        #only relevent if coming from tixel thresholding step
        if self.picNames[0] != None:
            for child in self.labelframe.winfo_children():
                if child.winfo_class() == 'Radiobutton':
                    child['state'] = 'disabled'



        
        self.blockSize_scale['state'] = tk.ACTIVE
        self.cMean_scale['state'] = tk.ACTIVE
        self.activateThresh_button['state'] = tk.DISABLED
        self.confirm_thresh['state'] = tk.ACTIVE
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<B1-Motion>')
        self.my_canvas.unbind('<ButtonRelease-1>')
        
        #finding the initial bw image from thresholding



        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, self.blockSize_value.get(), self.cMean_value.get())
        bw_image = Image.fromarray(thresh)
        sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(sized_bw)
        self.lmain.image = imgtk
        self.lmain.configure(image=imgtk)


    # "Open spatial folder" window
    def second_window(self):
        self.sendinfo_flag = False
        for i in self.names:
            if "meta" in i:
                self.json = self.folder_selected + "/" + i

            elif "list" in i:
                self.position = self.folder_selected + "/" + i

        try:
            self.excelName = self.metadata['run']
        except KeyError:
            self.excelName = "Test"

        self.newWindow.title("AtlasXbrowser (" + self.excelName+")")

        self.postB_Name = self.folder_selected + "/tissue_hires_image.png"
        a = Image.open(self.postB_Name)
        self.bar["value"] = 30
        self.pWindow.update()
        self.bar["value"] = 40
        self.pWindow.update()

        w, h = (a.width, a.height)
        self.width, self.height = (a.width, a.height)
        resizeNumber = self.screen_height - 60
        if h > resizeNumber:
            self.factor = resizeNumber/h
            newW = int(round(w*resizeNumber/h))
            floor = a.resize((newW, resizeNumber), Image.ANTIALIAS)
        else:
            floor = a
            self.factor = 1

        self.refactor = a
        self.newWidth = floor.width ; self.newHeight = floor.height
        
        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        self.bar["value"] = 50
        self.pWindow.update()
        self.bar["value"] = 60
        self.pWindow.update()
        try:
            self.scale_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = img
        self.bar["value"] = 80
        self.pWindow.update()
        self.imgA = ImageTk.PhotoImage(floor)
        self.picNames = [self.imgA, None]  


        #update canvas and frame
        self.my_canvas.config(width = floor.width, height= floor.height)
        self.lmain.destroy()
        self.newWindow.geometry("{0}x{1}".format(floor.width + 300, self.screen_height))
        self.right_canvas.config(width = floor.width + 300, height= h)
        try:
            newFactor = resizeNumber/self.metadata['rawHeight']
        except KeyError:
            newFactor = 1
        self.Rpoints = [i*newFactor for i in self.metadata['points']]

        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]
        self.arr = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]

        #Buttons
        self.begin_button['state'] = tk.DISABLED
        self.confirm_button['state'] = tk.DISABLED
        self.blockSize_scale['state'] = tk.DISABLED
        self.cMean_scale['state'] = tk.DISABLED
        self.grid_button["state"] = tk.ACTIVE
        self.gridA_button["state"] = tk.ACTIVE
        self.gridB_button['state'] = tk.DISABLED
        self.onoff_button["state"] = tk.DISABLED
        self.check_on = tk.IntVar()
        self.check_on.set(0)
        #tk.Radiobutton(self.right_canvas, text="Count On", variable=self.check_on, value=1, state=tk.DISABLED).place(relx=.5, rely=.68)
        self.update_file = tk.Button(self.right_canvas, text = "Update the Spatial folder", command = self.update_pos)
        self.update_file.place(relx=.11, rely= .9)

        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, int(self.metadata['blockSize']), int(self.metadata['threshold']))
        self.bar["value"] = 100
        self.pWindow.update()
        bw_image = Image.fromarray(thresh)
        sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(sized_bw)
        self.picNames.append(imgtk)
        self.my_canvas.create_image(0,0, anchor="nw", image = imgtk, state="disabled")
        self.pWindow.destroy()
        self.sendinfo(self.picNames[2])
        
    #Update Threshold sliders
    def showThresh(self, value):
        if float(value) > 11:
            self.my_canvas.delete("all")
        #sel set to block size value
            sel = int(self.blockSize_value.get())
        #sec set to C value
            sec = int(self.cMean_value.get())
            if sel %2 == 0:
                sel+=1
            
            #self.blockSize_label_value.config(text = str(sel), font =("Courier", 14))
            #self.cMean_label_value.config(text = str(sec), font =("Courier", 14))
            
        #re doing the thresholding for the newly set values
            thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, sel, sec)
            bw_image = Image.fromarray(thresh)
            sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            
        else:
            self.my_canvas.delete("all")
            #sel set to blocksize variable
            sel = int(self.blockSize_value.get())
            if sel %2 == 0:
                sel+=1
            #sec set to cMean variable
            sec = int(self.cMean_value.get())


            #new threshold created and loaded onto screen
            thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, sel, sec)
            bw_image = Image.fromarray(thresh)
            sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)

    #Find Roi coordinates
    def find_points(self):

        #Disable  buttons that should not be activated
        self.blockSize_scale['state'] = tk.DISABLED
        self.cMean_scale['state'] = tk.DISABLED
        self.begin_button['state'] = tk.DISABLED
        self.activateThresh_button['state'] = tk.DISABLED
        self.grid_button['state'] = tk.DISABLED
        self.gridA_button['state'] = tk.DISABLED
        self.gridB_button['state'] = tk.DISABLED
        self.onoff_button['state'] = tk.DISABLED

        self.lmain.destroy()
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgA, state="disabled")
        
        self.c = DrawShapes(self.my_canvas, self.quad_coords)
        self.my_canvas.bind('<Button-1>', self.c.on_click_quad)
        
        self.my_canvas.bind('<Button1-Motion>', self.c.on_motion)

        self.confirm_button["state"] = tk.ACTIVE

       

    #Confirms coordinates choosen 
    def confirm(self, none):
        self.ROILocated = True
        #self.fromOverlay = True
        self.activateThresh_button['state'] = tk.ACTIVE
        
        #List of Lists containing a list for every tixel
        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]

        self.arr = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]

        self.Rpoints = self.my_canvas.coords(self.c.current)
        self.quad_coords = self.my_canvas.coords(self.c.current)

        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgA, state="normal")
        self.my_canvas.unbind("<B1-Motion>")
        self.my_canvas.unbind("<Button-1>")

        self.confirm_button["state"] = tk.DISABLED
        self.begin_button["state"] = tk.ACTIVE
        self.grid_button["state"] = tk.ACTIVE
        self.gridA_button["state"] = tk.ACTIVE
        self.gridB_button["state"] = tk.ACTIVE
        self.onoff_button["state"] = tk.ACTIVE
            

    def save_thresholded_image(self):

        #if ROI is located enable tixel overlays, activate thresh button, and tixel thersholding
        if self.ROILocated:
            self.grid_button['state'] = tk.ACTIVE
            self.gridA_button['state'] = tk.ACTIVE
            self.gridB_button['state'] = tk.ACTIVE
            self.onoff_button['state'] = tk.ACTIVE
            self.activateThresh_button['state'] = tk.ACTIVE


        #activating the button to beging ROI location
        self.begin_button['state'] = tk.ACTIVE
        self.confirm_thresh['state'] = tk.DISABLED
        
        #ensuring blocksize is odd
        tvalue = self.blockSize_value.get()
        svalue = self.cMean_value.get()
        if tvalue %2 ==0:
            tvalue +=1

        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, tvalue, svalue)
        bwFile_Name = self.excelName + "BW.png"
        cv2.imwrite(bwFile_Name, thresh)
        bw = Image.open(bwFile_Name)
        sized_bw = bw.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        bw_Image = ImageTk.PhotoImage(sized_bw)

        #checking if there is already a bw_image and replacing it if so
        if (len(self.picNames) >= 3):
            #if it is replaced with the new bw_Image
            self.picNames[2] = bw_Image
        else:
            #otherwise the new image is added to the end, which will be the 2nd index
            self.picNames.append(bw_Image)

        return bw_Image

    def grid(self,pic):
        #if the lmain label exists, we are coming from thresholding
        if self.lmain.winfo_exists() == 1:
            self.lmain.destroy()
            self.activateThresh_button['state'] = "active"
            self.blockSize_scale['state'] = "disabled"
            self.cMean_scale['state'] = "disabled"
            
        self.value_sheFrame.set(1) 
        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = pic, state="disabled")
    
        ratioNum = (self.num_chan*2) - 1
        leftS = ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[6],self.Rpoints[7],ratioNum)
        topS = ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[2],self.Rpoints[3],ratioNum)
        slope = [round(leftS[1]-self.Rpoints[1], 5), round(leftS[0]-self.Rpoints[0], 5)]
        slopeT = [round(topS[1]-self.Rpoints[1], 5), round(topS[0]-self.Rpoints[0], 5)]


        slopeO = [slope[0]*2, slope[1]*2]
        slopeTO = [slopeT[0]*2, slopeT[1]*2]
        
        top = [0,0]
        left = [0,0]
        flag = False
        prev = [self.Rpoints[0],self.Rpoints[1]]
        excelC = 1
        for i in range(self.num_chan):
            top[0] = prev[0]+slopeT[1]
            top[1] = prev[1]+slopeT[0]
            flag = False
            
            for j in range(self.num_chan):
                if flag == False:
                    left[0] = prev[0]
                    left[1] = prev[1]
                    tL = [left[0],left[1]]
                    tR = [top[0],top[1]]
                    bL = [tL[0]+slope[1],tL[1]+slope[0]]
                    bR = [tR[0]+slope[1],tR[1]+slope[0]]
                    flag =  True
                else:
                    left[0] += slopeO[1]
                    left[1] += slopeO[0]
                    tL = [left[0],left[1]]
                    tR = [top[0],top[1]]
                    bL = [tL[0]+slope[1],tL[1]+slope[0]]
                    bR = [tR[0]+slope[1],tR[1]+slope[0]]
                position = str(j+1) + "x" + str(i)
                pointer = [tL[0],tL[1],    tR[0],tR[1],     bR[0],bR[1],   bL[0],bL[1],    tL[0],tL[1]]
                self.my_canvas.create_polygon(pointer, fill='', outline="black", tag = position, width=1, state="disabled")
                centerx, centery = center(tL,tR,bR,bL)
                self.coords[j][i].append(centerx/self.factor)
                self.coords[j][i].append(centery/self.factor)
                top[0] += slopeO[1]
                top[1] += slopeO[0]
                excelC += 1

                #allowing on and off tissues on overlay
                #if self.classification_active:
                if self.classification_active:
                    if self.arr[j][i] == 1:
                        try:
                            tags = self.my_canvas.find_withtag(position)
                            self.my_canvas.itemconfig(tags[0], fill='red', state="normal")
                        except IndexError:
                            self.my_canvas.itemconfig((self.num_chan*i+5)+j, fill='red', state="normal")
            prev[0] += slopeTO[1]
            prev[1] += slopeTO[0]

    #Send parameters to tissue_grid.py 
    def sendinfo(self,pic):
        self.classification_active = True

        #if the lmain label still exists, destroy it
        if self.lmain.winfo_exists() == 1:
            self.lmain.destroy()

        
        #self.activateThresh_button['state'] = tk.DISABLED
        self.check_on.set(0)
        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = pic, state="disabled")

        ratioNum = (self.num_chan*2) - 1
        leftS = ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[6],self.Rpoints[7],ratioNum)
        topS = ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[2],self.Rpoints[3],ratioNum)
        slope = [round(leftS[1]-self.Rpoints[1], 5), round(leftS[0]-self.Rpoints[0], 5)]
        slopeT = [round(topS[1]-self.Rpoints[1], 5), round(topS[0]-self.Rpoints[0], 5)]


        slopeO = [slope[0]*2, slope[1]*2]
        slopeTO = [slopeT[0]*2, slopeT[1]*2]
        
        top = [0,0]
        left = [0,0]
        flag = False
        prev = [self.Rpoints[0],self.Rpoints[1]]
        excelC = 1
        for i in range(self.num_chan):
            top[0] = prev[0]+slopeT[1]
            top[1] = prev[1]+slopeT[0]
            flag = False
            
            for j in range(self.num_chan):
                if flag == False:
                    left[0] = prev[0]
                    left[1] = prev[1]
                    tL = [left[0],left[1]]
                    tR = [top[0],top[1]]
                    bL = [tL[0]+slope[1],tL[1]+slope[0]]
                    bR = [tR[0]+slope[1],tR[1]+slope[0]]
                    flag =  True
                else:
                    left[0] += slopeO[1]
                    left[1] += slopeO[0]
                    tL = [left[0],left[1]]
                    tR = [top[0],top[1]]
                    bL = [tL[0]+slope[1],tL[1]+slope[0]]
                    bR = [tR[0]+slope[1],tR[1]+slope[0]]

                position = str(j+1) + "x" + str(i)
                pointer = [tL[0],tL[1],    tR[0],tR[1],     bR[0],bR[1],   bL[0],bL[1],    tL[0],tL[1]]
                self.my_canvas.create_polygon(pointer, fill='', outline="black", tag = position, width=1, state="disabled")
                centerx, centery = center(tL,tR,bR,bL)
                self.coords[j][i].append(centerx/self.factor)
                self.coords[j][i].append(centery/self.factor)
                top[0] += slopeO[1]
                top[1] += slopeO[0]
                excelC += 1
            prev[0] += slopeTO[1]
            prev[1] += slopeTO[0]


        if self.picNames[1] != None:
            #setting all tixel chaning radio buttons to on
            for child in self.labelframe.winfo_children():
                if child.winfo_class() == 'Radiobutton':
                    child['state'] = 'active'
            
            #setting the mouse to flip a single tixel at time, in accordance with option 1
            self.my_canvas.bind('<Button-1>',self.on_off)

            self.position_file["state"] = tk.ACTIVE
            self.begin_button['state'] = tk.DISABLED
            self.onoff_button["state"] = tk.DISABLED
            
            dbit = self.excelName + "BW.png"
            points_copy = self.Rpoints.copy()

            tissue_information = Tissue(points_copy, self.factor, dbit, self.num_chan)
            self.arr,self.spot_dia, self.fud_dia = tissue_information.theAnswer()
            for i in range(len(self.arr)):
                for j in range(len(self.arr)):
                    position = str(j+1) + "x" + str(i)

                    if self.arr[j][i] == 1:
                        try:
                            tags = self.my_canvas.find_withtag(position)
                            self.my_canvas.itemconfig(tags[0], fill='red', state="normal")
                        except IndexError:
                            self.my_canvas.itemconfig((self.num_chan*i+5)+j, fill='red', state="normal")
        else:
            for child in self.labelframe.winfo_children():
                if child.winfo_class() == 'Radiobutton':
                    child['state'] = 'active'
            if "tissue_positions_list_log_UMI_Genes.csv" in self.names:
                for child in self.sheframe.winfo_children():
                    if child.winfo_class() == 'Radiobutton':
                        child['state'] = 'active'
            self.my_canvas.unbind("<Button-1>")
            self.my_canvas.unbind("<B1-Motion>")
            self.my_canvas.unbind("<ButtonRelease-1>")
            self.my_canvas.bind('<Button-1>',self.on_off)

            self.update_file["state"] = tk.ACTIVE
            if self.sendinfo_flag == False:
                with open(self.folder_selected + "/tissue_positions_list.csv") as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for row in csv_reader:
                        j = int(row[3])+1
                        i = int(row[2])
                        if row[1] == "1":
                            self.arr[j-1][i] = 1
                            position = str(j)+"x"+str(i)
                            try:
                                tags = self.my_canvas.find_withtag(position)
                                self.my_canvas.itemconfig(tags[0], fill='red', state="normal")
                            except IndexError:
                                pass
                        else:
                            self.arr[j-1][i] = 0
                self.sendinfo_flag = True
            else:
                for i in range(len(self.arr)):
                    for j in range(len(self.arr)):
                        position = str(j+1) + "x" + str(i)
                        if self.arr[j][i] == 1:
                            try:
                                tags = self.my_canvas.find_withtag(position)
                                self.my_canvas.itemconfig(tags[0], fill='red', state="normal")
                            except IndexError:
                                self.my_canvas.itemconfig((self.num_chan*i+5)+j, fill='red', state="normal")
            self.onoff_button["state"] = tk.DISABLED

            

    """Functions used to update On/off Tissue ... creates a new quadrilateral"""
    def offon(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<B1-Motion>')
        self.my_canvas.unbind('<ButtonRelease-1>')
        self.my_canvas.bind('<Button-1>',self.on_off)
    def highlit(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.bind('<Button-1>',self.highlight)
        self.my_canvas.bind('<B1-Motion>', self.update_sel_rect)    
    def update_sel_rect(self, event):
        self.my_canvas.bind("<ButtonRelease-1>", self.release)
        self.botx, self.boty = event.x, event.y
        self.my_canvas.coords("highlight", self.topx, self.topy, self.botx, self.boty)  # Update selection rect.
    def highlight(self, event):
        self.topx, self.topy = event.x, event.y
        self.my_canvas.create_rectangle(self.topx, self.topy, self.topx, self.topy,dash=(2,2), fill='', tag= "highlight", outline='black')
    def release(self,event):
        for k in self.my_canvas.find_overlapping(self.topx, self.topy, self.botx, self.boty):
            position = event.widget.gettags(k)
            if len(position) > 0 and position[0]!="highlight":
                try:
                    where = position[0].split("x")
                except IndexError:
                    break
                
                state = self.my_canvas.itemcget(k,'state')
                i = where[0]
                j = where[1]
                if self.check_on.get() == 0:
                    if state == "normal":
                        self.my_canvas.itemconfig(k, fill="", state="disabled", width=1)
                        self.arr[int(i)-1][int(j)] = 0
                    else:
                        self.my_canvas.itemconfig(k, fill="red", state ="normal", width=1)
                        self.arr[int(i)-1][int(j)] = 1
                else:
                    if state == "normal":
                        self.my_canvas.itemconfig(k, state="disabled", outline="")
                        self.arr[int(i)-1][int(j)] = 0
                    else:
                        self.my_canvas.itemconfig(k, state ="normal", width=1, outline="black")
                        self.arr[int(i)-1][int(j)] = 1

        self.my_canvas.coords("highlight", 0,0,0,0)
        self.my_canvas.unbind("<ButtonRelease-1>")
    def highliton(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.bind('<Button-1>',self.highlight)
        self.my_canvas.bind('<B1-Motion>', self.update_sel_recton)
    def update_sel_recton(self, event):
        self.my_canvas.bind("<ButtonRelease-1>", self.releaseon)
        self.botx, self.boty = event.x, event.y
        self.my_canvas.coords("highlight", self.topx, self.topy, self.botx, self.boty)  # Update selection rect.
    def releaseon(self,event):
        for k in self.my_canvas.find_overlapping(self.topx, self.topy, self.botx, self.boty):
            position = event.widget.gettags(k)
            if len(position) > 0 and position[0]!="highlight":
                try:
                    where = position[0].split("x")
                except IndexError:
                    break
                i = where[0]
                j = where[1]
                if self.check_on.get() == 0:
                    self.my_canvas.itemconfig(k, fill="red", state ="normal", width=1)
                    self.arr[int(i)-1][int(j)] = 1
                else:
                    self.my_canvas.itemconfig(k, width=1, state ="normal", outline="black")
                    self.arr[int(i)-1][int(j)] = 1

        self.my_canvas.coords("highlight", 0,0,0,0)
        self.my_canvas.unbind("<ButtonRelease-1>")
    def highlitoff(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.bind('<Button-1>',self.highlight)
        self.my_canvas.bind('<B1-Motion>', self.update_sel_rectoff)
    def update_sel_rectoff(self, event):
        self.my_canvas.bind("<ButtonRelease-1>", self.releaseoff)
        self.botx, self.boty = event.x, event.y
        self.my_canvas.coords("highlight", self.topx, self.topy, self.botx, self.boty)  # Update selection rect.
    def releaseoff(self,event):
        for k in self.my_canvas.find_overlapping(self.topx, self.topy, self.botx, self.boty):
            position = event.widget.gettags(k)
            if len(position) > 0 and position[0]!="highlight":
                try:
                    where = position[0].split("x")
                except IndexError:
                    break
                i = where[0]
                j = where[1]
                if self.check_on.get() == 0:
                    self.my_canvas.itemconfig(k, fill="", state="disabled", width=1)
                    self.arr[int(i)-1][int(j)] = 0
                else:
                    self.my_canvas.itemconfig(k, state="disabled", outline="")
                    self.arr[int(i)-1][int(j)] = 0

        self.my_canvas.coords("highlight", 0,0,0,0)
        self.my_canvas.unbind("<ButtonRelease-1>")
    def on_off(self, event):
        tag = event.widget.find_closest(event.x,event.y)
        position = event.widget.gettags(tag)
        try:
            where = position[0].split("x")
        except IndexError:
            return None
        state = self.my_canvas.itemcget(tag,'state')
        i = where[0]
        j = where[1]
        if self.check_on.get()==0:
            if state == "normal":
                self.my_canvas.itemconfig(tag, fill="", state="disabled", width=1)
                self.arr[int(i)-1][int(j)] = 0
                self.numTixels -= 1
            else:
                self.my_canvas.itemconfig(tag, fill="red", state ="normal", width=1)
                self.arr[int(i)-1][int(j)] = 1
                self.numTixels += 1
        else:
            if state == "normal":
                self.my_canvas.itemconfig(tag, state="disabled", outline="")
                self.arr[int(i)-1][int(j)] = 0
                self.numTixels -= 1
            else:
                self.my_canvas.itemconfig(tag, state ="normal", width=1, outline="black")
                self.arr[int(i)-1][int(j)] = 1
                self.numTixels += 1

        


    #Creates files for spatial folder
    #Creates files for spatial folder
    def create_files(self):
        try:
            path = os.path.join(self.folder_selected, "spatial")
            os.mkdir(path)
        except FileExistsError:
            path = self.folder_selected + "/spatial"

        # barcode_file = "bc" + str(self.num_chan) + "v" + self.barcodes + ".txt"
        my_file = open(self.barcode_filename,"r")
        excelC = 1
        with open(path + "/tissue_positions_list.csv", 'w') as f:
            writer = csv.writer(f)
            self.numTixels = 0
            for i in range(self.num_chan):
                for j in range(self.num_chan):
                    barcode = my_file.readline().split('\t')
                    if self.arr[j][i] == 1:
                        self.numTixels+=1
                        writer.writerow([barcode[0].strip(), 1, i, j, self.coords[j][i][1], self.coords[j][i][0]])
                    else:
                        writer.writerow([barcode[0].strip(), 0, i, j, self.coords[j][i][1], self.coords[j][i][0]])

                excelC += 1
              
        my_file.close()
        self.json_file(path)
        self.grid_button["state"] = tk.DISABLED
        self.gridA_button["state"] = tk.DISABLED
        try: 
            move(self.figure_folder,path)
        except shutil.Error:
            rmtree(path+"/"+"figure")
            move(self.figure_folder,path)
        f.close()
        bwFile_Name = self.excelName + "BW.png"
        os.remove(bwFile_Name)
        mb.showinfo("Congratulations!", "The spatial folder is created!")
        

    #Creates Metadata.json
    def json_file(self,path):
        factorHigh = 0
        factorLow = 0

        if self.width > self.height:
            factorHigh = 2000/self.width
            factorLow = 600/self.width
            high_res = self.refactor.resize((2000, int(self.height*factorHigh)), Image.ANTIALIAS)
            low_res = self.refactor.resize((600, int(self.height*factorLow)), Image.ANTIALIAS)
        else:
            factorHigh = 2000/self.height
            factorLow = 600/self.height
            high_res = self.refactor.resize((int(self.width*factorHigh), 2000), Image.ANTIALIAS)
            low_res = self.refactor.resize((int(self.width*factorLow), 600), Image.ANTIALIAS)

        high_res.save(path+"/tissue_hires_image.png")
        low_res.save(path+"/tissue_lowres_image.png")
        
        dictionary = {"spot_diameter_fullres": self.spot_dia,
                        "tissue_hires_scalef": factorHigh, 
                        "fiducial_diameter_fullres": self.fud_dia,
                        "tissue_lowres_scalef": factorLow}
        sel = int(self.blockSize_value.get())
        if sel %2 == 0:
            sel+=1
        sec = int(self.cMean_value.get())
        points_Raw = [i/self.factor for i in self.Rpoints]
        metaDict = {"points" : points_Raw,
                    "blockSize": sel,
                    "threshold": sec,
                    "numTixels": self.numTixels,
                    "rawHeight": self.rawHeight,
                    "numChannels": self.num_chan
                    }
        metaDict.update(self.metadata)
        
        json_object = json.dumps(dictionary, indent = 4)
        with open(path+"/scalefactors_json.json", "w") as outfile:
            outfile.write(json_object)
            outfile.close()
        meta_json_object = json.dumps(metaDict, indent = 4)
        with open(path+"/metadata.json", "w") as outfile:
            outfile.write(meta_json_object)
            outfile.close()

    
    #Update changes to tissue_positions_list.csv
    def update_pos(self):
        p = open(self.folder_selected + "/metadata.json")
        meta = json.load(p)

        barcode_lis = []
        with open(self.folder_selected + "/tissue_positions_list.csv", "r") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            for row in reader:
                curr_barcode = row[0]
                barcode_lis.append(curr_barcode)
            
        csv_file.close()
            
        with open(self.folder_selected + "/tissue_positions_list.csv", 'w') as f:
            writer = csv.writer(f)

            for i in range(self.num_chan):
                for j in range(self.num_chan):
                    
                    inx = (i * self.num_chan) + j
                    # print(barcode_lis[inx].strip())
                    if self.arr[j][i] == 1:
                        writer.writerow([barcode_lis[inx].strip(), 1, i, j, self.coords[j][i][1]/self.tissue_hires_scalef, self.coords[j][i][0]/self.tissue_hires_scalef])
                    else:
                        writer.writerow([barcode_lis[inx].strip(), 0, i, j, self.coords[j][i][1]/self.tissue_hires_scalef, self.coords[j][i][0]/self.tissue_hires_scalef])

        f.close()
        meta['numTixels'] = self.numTixels
        meta_json_object = json.dumps(meta, indent = 4)
        with open(self.folder_selected+ "/metadata.json", "w") as outfile:
            outfile.write(meta_json_object)
            outfile.close()
        
        mb.showinfo("Congratulations!", "The spatial folder has been updated!")

    #Create colorscheme for UMI/Gene count when loading tissue_positions_list_log_UMI_Genes.csv
    def count(self,which):
        name = ""
        if len(self.right_canvas.gettags("name0")) > 0:
            self.right_canvas.delete("name0")
            self.right_canvas.delete("name1")
            self.right_canvas.delete("name2")
            self.right_canvas.delete("name3")
            self.right_canvas.delete("name4")

        self.check_on.set(1)
        my_data = np.genfromtxt(self.folder_selected + "/tissue_positions_list_log_UMI_Genes.csv", delimiter=",")
        min_value = my_data.min(axis=0)[which]
        max_value = my_data.max(axis=0)[which]
        CBleft = min_value;
        with open(self.folder_selected + "/tissue_positions_list_log_UMI_Genes.csv", 'r') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                j = int(row[3])+1
                i = int(row[2])
                count = float(row[which])
                position = str(j)+"x"+str(i)
                level = round((count-CBleft)/(max_value-CBleft)*50)
                cmap = matplotlib.cm.get_cmap('jet', 50)
                rgba = cmap(level)
                new = [round(i * 255) for i in rgba[:-1]]
                var = from_rgb(new)
                if self.arr[j-1][i] == 1:
                    self.my_canvas.itemconfig(position, fill=var, width="1", state="normal")
                else:
                    self.my_canvas.itemconfig(position, fill=var, outline="", state="disabled")
        f.close()

        numsteps = 6
        colorbarLog = np.linspace(min_value, max_value, numsteps)
        colorbarNorm = [round(math.exp(i)-1) for i in colorbarLog]
        xvalues = np.linspace(15, 205, numsteps)
        yValue = 40

        self.cbframe = tk.LabelFrame(self.right_canvas, text="Colorbar", padx="5px", pady="14px")
        self.cbframe.place(relx=.11, rely=.23)

        c = tk.Canvas(self.cbframe, width=220, height=50)
        c.pack()
        c.delete("all")
        for i in range(len(colorbarNorm)):
            name = "name"
            name += str(i)
            c.create_text(xvalues[i], yValue, text = str(colorbarNorm[i]), font =("Courier", 14), angle = 70, anchor = "w", tag=name)

        # colorBar
        bar = Image.open("colorbar.png")
        resized_bar = bar.resize((200, 40), Image.ANTIALIAS)
        color = ImageTk.PhotoImage(resized_bar)
        self.color_bar = tk.Label(self.cbframe, image=color)
        self.color_bar.pack()
        self.color_bar.image = color
        self.color_bar.configure(image=color)
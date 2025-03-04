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
        resized_image = background_image.resize((int(self.screen_width/1.5), self.screen_height), Image.LANCZOS)
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
        self.tixel_status = None
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
        self.tixel_width = .5
        self.ROILocated = False
        self.current_image_id = 0
        
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

        #Rotation Panel
        self.rotate_45_90 = tk.IntVar()
        self.rotate_45_90.set(90)
        self.rotateframe = tk.LabelFrame(self.right_canvas, text="Rotation", padx=10, pady=10)
        self.rotateframe.place(relx=.11, rely=0)
        self.image_updated = tk.Button(self.rotateframe, text = "Confirm", command = self.confirm_rotation, state=tk.DISABLED)
        self.image_updated.pack(side = tk.BOTTOM, anchor=tk.W)
        rotateleft = Image.open("rotateleft.png")
        bg = ImageTk.PhotoImage(rotateleft)
        self.left = tk.Button(self.rotateframe, image=bg, command= lambda:self.rotate_image(0), state=tk.DISABLED)
        self.left.image = bg
        self.left.pack(side=tk.LEFT)
        rotateright = Image.open("rotateright.png")
        bg2 = ImageTk.PhotoImage(rotateright)
        self.right = tk.Button(self.rotateframe, image=bg2, command= lambda:self.rotate_image(1), state=tk.DISABLED)
        self.right.image = bg2
        self.right.pack(side=tk.LEFT)
        tk.Radiobutton(self.rotateframe, text="90", value=90, variable=self.rotate_45_90).pack(padx=(20, 0))
        tk.Radiobutton(self.rotateframe, text="45", value=45, variable=self.rotate_45_90).pack(padx=(20, 0))
        
        self.change_radio_rotationdegree_state(False)
        # rotate_left_small = Image.open("rotateleft2.png")
        # img3 = ImageTk.PhotoImage(rotate_left_small)
        # self.degree_45 = tk.Button(self.rotateframe, image = img3, command = lambda:self.image_axis(2), state=tk.DISABLED)
        # self.degree_45.image = img3
        # self.degree_45.pack(side=tk.LEFT)
        
        #f/crop
        self.cropframe = tk.LabelFrame(self.right_canvas, text="Cropping", padx="10px", pady="10px")
        self.cropframe.place(relx=.11, rely=.13)
        self.activateCrop_button = tk.Button(self.cropframe, text = "Activate", command = self.cropping, state=tk.DISABLED)
        self.activateCrop_button.pack(side=tk.LEFT)
        self.confirmCrop_button = tk.Button(self.cropframe, text = "Confirm", command = self.confirm_cropping, state=tk.DISABLED)
        self.confirmCrop_button.pack()


        #create Scales
        self.adframe = tk.LabelFrame(self.right_canvas, text="Adaptive Thresholding", padx="10px", pady="10px")
        self.adframe.place(relx=.11, rely=.21)

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
        self.thframe.place(relx=.11, rely= .39)
        self.begin_button = tk.Button(self.thframe, text = "Activate", command = self.activate_roi_determination, state=tk.DISABLED)
        self.begin_button.pack(side=tk.LEFT)

        self.confirm_button = tk.Button(self.thframe, text = "Confirm", command = lambda: self.confirm_roi(), state=tk.DISABLED)
        self.confirm_button.pack()

        self.shframe = tk.LabelFrame(self.right_canvas, text="Overlay", padx="10px", pady="10px")
        self.shframe.place(relx=.11, rely=.48)

        self.grid_button = tk.Button(self.shframe, text = "BW", command = lambda: self.grid(self.picNames[2], 2, 'reg'), state=tk.DISABLED)
        self.grid_button.pack(side=tk.LEFT)

        self.gridB_button = tk.Button(self.shframe, text = "BSA", command = lambda: self.grid(self.picNames[1], 1, 'reg'), state=tk.DISABLED)
        self.gridB_button.pack(side=tk.RIGHT)

        self.gridA_button = tk.Button(self.shframe, text = "postB", command = lambda: self.grid(self.picNames[0], 0, 'reg'), state=tk.DISABLED)
        self.gridA_button.pack(side=tk.RIGHT)

        self.quad_frame = tk.LabelFrame(self.right_canvas, text="Quadrants", padx="7px", pady="7px")
        self.quad_frame.place(relx=.11, rely=.57)
        
        self.one_quad = tk.Button(self.quad_frame, text="TL", command= lambda:self.show_quadrant(0), state=tk.DISABLED)
        self.one_quad.pack(side=tk.LEFT)
        
        self.two_quad = tk.Button(self.quad_frame, text="TR", command= lambda:self.show_quadrant(1), state=tk.DISABLED)
        self.two_quad.pack(side=tk.LEFT)
        
        self.four_quad = tk.Button(self.quad_frame, text="BR", command= lambda:self.show_quadrant(3), state=tk.DISABLED)
        self.four_quad.pack(side=tk.RIGHT)

        self.three_quad = tk.Button(self.quad_frame, text="BL", command= lambda:self.show_quadrant(2), state=tk.DISABLED)
        self.three_quad.pack(side=tk.RIGHT)

        self.labelframe = tk.LabelFrame(self.right_canvas, text="On/Off Tissue", padx="10px", pady="10px")
        self.labelframe.place(relx=.11, rely= .65)
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
        self.sheframe.place(relx=.11, rely= .85)
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
        self.position_file.place(relx=.11, rely= .94)        

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


        # label2 = tk.Label(self.starting_window, 
        # text = "Select PostB image:", 
        # font = ("Courier", 14),
        # # width = 25,
        # )
        # label2.grid(row = 1, column = 0, sticky = "e")
        # #label to display the name of the selected postB file to user

        # label2a = tk.Label(self.starting_window)
        # label2a.grid(row = 1, column =2, sticky = "w")

        # #attibute to store postB image file name
        # self.user_selected_postB = ""
        # #button where user can select postB
        # postB_button = tk.Button(self.starting_window, text = "File", command = lambda: self.get_image_file(1, label2a))
        # postB_button.grid(row = 1, column = 1, sticky = "w")


        #barcode file selection
         # standard barcode 1 automatically selected. Can also designate a custom file.
        label3 = tk.Label(self.starting_window,
        text = "Barcode File:",
        font = ("Courier", 14))
        label3.grid(row = 2, column = 0, sticky = "e")

        label3a = tk.Label(self.starting_window,
        text = "bc50v1-24" 
        )
        label3a.grid(row = 2, column = 1, sticky="w")        

        # label3b = tk.Label(self.starting_window)
        # label3b.grid(row = 2, column = 3, sticky = "w")

        revert_button = tk.Button(self.starting_window, text="Revert to bc50v1-24", bg="red", command=lambda: self.use_barcode1(revert_button, barcode_button))

        barcode_button = tk.Button(self.starting_window, text = "bc50v1-24",bg="grey" ,command = lambda: self.get_barcode_file(barcode_button, revert_button))
        barcode_button.grid(row = 2, column = 1, sticky = "w")

        label3.grid(row = 2, column = 0, sticky = "e")

        self.run_identifier = tk.StringVar()
        label4 = tk.Label(self.starting_window, 
        text = "Run ID:", 
        font = ("Courier", 14)
        # width = 25
        )

        entry_box = tk.Entry(self.starting_window, textvariable = self.run_identifier,
        )
        label4.grid(row=3, column=0, sticky="e")
        entry_box.grid(row=3, column=1, sticky="w")

        #submit button
        button = tk.Button(self.starting_window, text='Submit', font =("Courier", 14), command = lambda: self.configure_metadata())
        button.grid(row = 5, column = 1, sticky = "w", pady = 20)

        #error button
        self.error_label = tk.Label(self.starting_window)
        self.error_label.grid(row = 6, column = 1, sticky = "w")

    def split_image(self, og_width):
        """Split the image into 4 quadrants and return them."""
        self.split_image_dict = {}
        crop_size = og_width // 2
        self.match_tixel_quad = {0: [0,0],
                                 1: [-og_width, 0],
                                 2: [0, -og_width],
                                 3: [-og_width, -og_width]
                                }
        original_pillow_images = [self.postb_resize_current.copy(), self.bsa_resize_current.copy(), self.bw_cropped_image.copy()]
        self.crop_scale_factor = crop_size / self.width_post_crop_resized
        for i in range(len(original_pillow_images)):
            img = original_pillow_images[i]
            width = img.width
            height = img.height
            quadrants = [
                img.crop((0, 0, width // 2, height // 2)).resize((self.width_post_crop_resized, 
                                                                  self.height_post_crop_resized), Image.LANCZOS),  # Top-left
                img.crop((width // 2, 0, width, height // 2)).resize((self.width_post_crop_resized,
                                                                      self.height_post_crop_resized), Image.LANCZOS),  # Top-right
                img.crop((0, height // 2, width // 2, height)).resize((self.width_post_crop_resized,
                                                                       self.height_post_crop_resized), Image.LANCZOS),  # Bottom-left
                img.crop((width // 2, height // 2, width, height)).resize((self.width_post_crop_resized,
                                                                           self.height_post_crop_resized), Image.LANCZOS),  # Bottom-right
            ]
            self.split_image_dict[i] = [ImageTk.PhotoImage(q) for q in quadrants]

    def show_quadrant(self, index):
        """Display the selected quadrant on the canvas."""
        self.current_quad_id = index
        quad_image = self.split_image_dict[self.current_image_id][index]
        self.grid(quad_image, self.current_image_id, 'quad')


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
                if int(barcodes) > 180:
                    self.tixel_width = .1
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
            self.user_selected_bsa = file
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
        #retrieving variables from stored StringVar variables
        runID = self.run_identifier.get()
        if runID != "":
            if self.custom_barcode_valid or self.custom_barcode_selected == False:
                val = self.user_selected_bsa.rfind("/")
                self.bsa_short = self.user_selected_bsa[val + 1: ]
                self.folder_selected = self.user_selected_bsa[:val]
                self.postB_short = "{}_postB.tif".format(runID)
                self.metadata = {
                "run": runID
                }
                #setting excelName var, used later, to equal the user specifed run ID
                self.excelName = runID

                #calling method that puts images on canvas
                self.configure_images()

                self.starting_window.destroy()
                # self.activateCrop_button['state'] = tk.ACTIVE
                self.newWindow.title("AtlasXbrowser (" + runID + ")")
                self.filemenu.entryconfig("Begin Image Processing", state = "disabled")
                self.filemenu.entryconfig("Open Spatial Folder", state = "disabled")

                self.left['state'] = tk.ACTIVE
                self.right['state'] = tk.ACTIVE
                # self.degree_45["state"] = tk.ACTIVE
                self.image_updated['state'] = tk.ACTIVE
                self.confirmCrop_button['state'] = tk.DISABLED

                self.change_radio_rotationdegree_state(True)
        else:
            self.error_label.config(text = "Error! Enter a Run Identifier!")
    
    def change_radio_rotationdegree_state(self, on):
        for child in self.rotateframe.winfo_children():
            if child.winfo_class() == 'Radiobutton':
                state = "disabled"
                if on:
                    state = "active"
                child['state'] = state 

    def configure_images(self):
        self.bsa_on_screen = Image.open(self.user_selected_bsa)

        w, h = (self.bsa_on_screen.width, self.bsa_on_screen.height)
        newH = self.screen_height - 60
        # self.image_array = cv2.imread(self.user_selected_bsa, 0)
        # self.rotation_matrix = np.identity(len(self.image_array))

        #find ratio of 60 less than screenheight to the image height
        self.factor = newH/h
        #use ratio to calcuate the new width
        newW = int(round(w*self.factor))
        #resize the bsa image based on these calculations
        bsa = self.bsa_on_screen.resize((newW, newH), Image.LANCZOS)
        self.bsa_tkinter_image = ImageTk.PhotoImage(bsa)

        self.lmain.pack()
        self.lmain.image = self.bsa_tkinter_image 
        self.lmain.configure(image = self.bsa_tkinter_image)

        self.bsa_resized = np.array(bsa)
        # print("Original height: {} width: {}".format(self.bsa_on_screen.height, self.bsa_on_screen.width))
        # print("New height: {} new width: {}".format(newH, newW))
        # print("Screen Height: {} screen width: {}".format(self.screen_height, self.screen_width))
        # w = self.bsa_on_screen.width()



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
                self.spatial_selected()
            except FileNotFoundError:
                mb.showwarning("Error", "metadata.json file is not present")
                self.pWindow.destroy()
        else:
            #Add error message
            pass
            

    #Initalize images that will be in container 
    def init_images(self):

        #opening images directly from previously stored path
        # a = self.bsa_cropped_pillow
        # b = self.postB_cropped_pillow

        self.width_post_crop, self.height_post_crop = (self.bsa_cropped_pillow.width, self.bsa_cropped_pillow.height)
        self.rawHeight = self.height_post_crop
        self.height_post_crop_resized = self.screen_height - 60
        self.factor = self.height_post_crop_resized/self.height_post_crop

        self.width_post_crop_resized = int(round(self.width_post_crop*self.factor))
        resized_bsa = self.bsa_cropped_pillow.resize((self.width_post_crop_resized, self.height_post_crop_resized), Image.LANCZOS)
        resized_postB = self.postB_cropped_pillow.resize((self.width_post_crop_resized, self.height_post_crop_resized), Image.LANCZOS)
        self.postb_resize_current = resized_postB
        self.bsa_resize_current = resized_bsa
        img = cv2.imread(self.postB_figure_path, cv2.IMREAD_UNCHANGED)
        flippedImage = img

        try:
            self.scale_image = cv2.cvtColor(flippedImage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedImage  

        self.bsa_post_crop_resized_tk = ImageTk.PhotoImage(resized_bsa)
        self.postB_post_crop_resized_tk = ImageTk.PhotoImage(resized_postB)
        self.picNames = [self.postB_post_crop_resized_tk, self.bsa_post_crop_resized_tk]

        # my_canvas populated with the BSA stained image instead of the post-B image
        self.lmain.pack()
        self.my_canvas.config(width = self.width_post_crop_resized, height= self.width_post_crop_resized)
        self.lmain.configure(image=self.bsa_post_crop_resized_tk)
        self.newWindow.geometry("{0}x{1}".format(self.width_post_crop_resized + 300, self.screen_height))
        self.right_canvas.config(width = self.width_post_crop_resized + 300, height= self.height_post_crop)

    #Rotate and flip the images
    def rotate_image(self, num):
        (h,w) = self.bsa_resized.shape[:2]
        cX, cY = (w // 2, h //2)
        degree_rot = self.rotate_45_90.get()
        if num == 0:
            self.rotated_degree += degree_rot 
        if num == 1:
            rot_clock = 360 - degree_rot
            self.rotated_degree += rot_clock 
        
        M = cv2.getRotationMatrix2D((cX, cY), self.rotated_degree, 1.0) 
        updated = cv2.warpAffine(self.bsa_resized, M, (w,h))
        formatted = Image.fromarray(updated)
        sized = formatted.resize((w, h), Image.LANCZOS)
        self.bsa_tkinter_image = ImageTk.PhotoImage(sized)
        self.lmain.image = self.bsa_tkinter_image
        self.lmain.configure(image=self.bsa_tkinter_image)

    #Update postB and BSA images to new image orientation 
    def confirm_rotation(self):
        self.create_figure_folder()
        self.left['state'] = tk.DISABLED
        self.right['state'] = tk.DISABLED
        # self.degree_45['state'] = tk.DISABLED
        self.image_updated['state'] = tk.DISABLED
        self.activateCrop_button['state'] = tk.ACTIVE
        self.change_radio_rotationdegree_state(False)

        self.prep_cropping()

    def prep_cropping(self):
        self.lmain.pack_forget()
        self.my_canvas.create_image(0, 0, image = self.bsa_tkinter_image, anchor="nw", tag = "image")

    def cropping(self):
        #creating cropping square on screen, defined as b
        self.b = DrawSquare(self.my_canvas)
        self.my_canvas.bind('<Button1-Motion>', self.b.on_motion)
        self.my_canvas.bind('<ButtonRelease-1>', self.b.on_release)

        #deactivating the 'activate' button, activating the 'confirm' button
        self.activateCrop_button['state'] = tk.DISABLED
        self.confirmCrop_button['state'] = tk.ACTIVE

    def create_figure_folder(self):
        self.figure_folder = os.path.join(self.folder_selected, "figure") 
        #try making a figure folder
        try:
            os.mkdir(self.figure_folder)
        #exception if the folder already exists. If so, remove and remake
        except FileExistsError:
            rmtree(self.figure_folder)
            os.mkdir(self.figure_folder)

        self.bsa_figure_path = self.figure_folder + "/" + self.bsa_short
        self.postB_figure_path = self.figure_folder + "/" + self.postB_short

    #Confirm cropping and reinitalize images in the containers
    def confirm_cropping(self):
        #source is the source folder of the spatial images
        source = self.folder_selected
        coords = self.my_canvas.coords('crop')
        image1 = cv2.imread(self.user_selected_bsa)
        (h, w) = image1.shape[:2]
        cX, cY = (w // 2, h //2)
        degrees = self.rotated_degree % 360
        M = cv2.getRotationMatrix2D((cX, cY), degrees, 1.0)
        rot_image1 = cv2.warpAffine(image1, M, (w, h))
        I = cv2.cvtColor(rot_image1, cv2.COLOR_BGR2RGB)
        img1 = Image.fromarray(I)
        self.bsa_cropped_pillow = img1.crop((int(coords[0]/self.factor),int(coords[1]/self.factor),int(coords[2]/self.factor),int(coords[3]/self.factor)))
        bsa = self.bsa_cropped_pillow.save(self.bsa_figure_path)

        # self.postB_figure_path = self.figure_folder + "/" + self.postB_short
        image2 = np.asarray(self.bsa_cropped_pillow)
        postB_cropped = image2[:, :, 2]
        self.postB_cropped_pillow = Image.fromarray(postB_cropped)
        # rot_image2 = cv2.warpAffine(image2, M, (w,h))
        # img2 = Image.fromarray(rot_image2)
        # im2 = img2.crop((int(coords[0]/self.factor),int(coords[1]/self.factor),int(coords[2]/self.factor),int(coords[3]/self.factor))) 
        post = self.postB_cropped_pillow.save(self.postB_figure_path)

        self.metadata["orientation"] = {"rotation": degrees}
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<Button1-Motion>') 

        self.my_canvas.delete("all")

        self.activateThresh_button['state'] = tk.ACTIVE
        self.confirmCrop_button['state'] = tk.DISABLED
        self.init_images()
                        
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
            self.one_quad["state"] = tk.DISABLED
            self.two_quad["state"] = tk.DISABLED
            self.three_quad["state"] = tk.DISABLED
            self.four_quad["state"] = tk.DISABLED
            
            
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
        # print("bw width: {} height: {}".format(bw_image.width, bw_image.height))
        sized_bw = bw_image.resize((self.width_post_crop_resized, self.height_post_crop_resized), Image.LANCZOS)
        self.bw_cropped_image = sized_bw
        self.split_image(self.width_post_crop_resized)
        # print("bw width: {} height: {}".format(sized_bw.width, sized_bw.height))
        imgtk = ImageTk.PhotoImage(sized_bw)
        self.lmain.image = imgtk
        self.lmain.configure(image=imgtk)

    # "Open spatial folder" window
    def spatial_selected(self):
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
        hi_res_postB = Image.open(self.postB_Name)
        self.bar["value"] = 30
        self.pWindow.update()
        self.bar["value"] = 40
        self.pWindow.update()

        self.width_hires_postB, self.height_hires_postB = (hi_res_postB.width, hi_res_postB.height)
        # self.width, self.height = (a.width, a.height)
        resizeNumber = self.screen_height - 60
        if self.height_hires_postB > resizeNumber:
            self.factor = resizeNumber/self.height_hires_postB
            newW = int(round(self.width_hires_postB * self.factor))
            resized_postB = hi_res_postB.resize((newW, resizeNumber), Image.LANCZOS)
        else:
            # floor = hi_res_postB
            resized_postB = hi_res_postB
            self.factor = 1

        # self.refactor = hi_res_postB
        self.postB_cropped_pillow = hi_res_postB
        self.resized_width = resized_postB.width
        self.resized_height = resized_postB.height
        
        # img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        postB_array = np.array(hi_res_postB)
        self.bar["value"] = 50
        self.pWindow.update()
        self.bar["value"] = 60
        self.pWindow.update()
        try:
            self.postB_array_scaled = cv2.cvtColor(postB_array, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.postB_array_scaled = postB_array
        self.bar["value"] = 80
        self.pWindow.update()
        self.resized_hires_postB = ImageTk.PhotoImage(resized_postB)
        self.picNames = [self.resized_hires_postB, None]  


        #update canvas and frame
        self.my_canvas.config(width = self.resized_width, height= self.resized_height)
        self.lmain.destroy()
        self.newWindow.geometry("{0}x{1}".format(self.resized_width + 300, self.screen_height))
        self.right_canvas.config(width = self.resized_width + 300, height= self.height_hires_postB)
        try:
            newFactor = resizeNumber/self.metadata['rawHeight']
        except KeyError:
            newFactor = 1
        self.Rpoints = [i*newFactor for i in self.metadata['points']]

        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]
        self.tixel_status = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]

        #Buttons
        self.begin_button['state'] = tk.DISABLED
        self.confirm_button['state'] = tk.DISABLED
        self.blockSize_scale['state'] = tk.DISABLED
        self.cMean_scale['state'] = tk.DISABLED
        self.grid_button["state"] = tk.ACTIVE
        self.gridA_button["state"] = tk.ACTIVE
        self.gridB_button['state'] = tk.DISABLED
        self.onoff_button["state"] = tk.DISABLED
        self.one_quad["state"] = tk.ACTIVE
        self.two_quad["state"] = tk.ACTIVE
        self.three_quad["state"] = tk.ACTIVE
        self.four_quad["state"] = tk.ACTIVE
        self.check_on = tk.IntVar()
        self.check_on.set(0)
        #tk.Radiobutton(self.right_canvas, text="Count On", variable=self.check_on, value=1, state=tk.DISABLED).place(relx=.5, rely=.68)
        self.update_file = tk.Button(self.right_canvas, text = "Update the Spatial folder", command = self.update_pos)
        self.update_file.place(relx=.11, rely= .94)

        thresh = cv2.adaptiveThreshold(self.postB_array_scaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, int(self.metadata['blockSize']), int(self.metadata['threshold']))
        self.bar["value"] = 100
        self.pWindow.update()
        bw_image = Image.fromarray(thresh)
        sized_bw = bw_image.resize((self.resized_width, self.resized_height), Image.LANCZOS)
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
            sized_bw = bw_image.resize((self.width_post_crop_resized, self.height_post_crop_resized), Image.LANCZOS)
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
            sized_bw = bw_image.resize((self.width_post_crop_resized, self.height_post_crop_resized), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)

    #Find Roi coordinates
    def activate_roi_determination(self):
        #Disable  buttons that should not be activated
        self.blockSize_scale['state'] = tk.DISABLED
        self.cMean_scale['state'] = tk.DISABLED
        self.begin_button['state'] = tk.DISABLED
        self.activateThresh_button['state'] = tk.DISABLED
        self.grid_button['state'] = tk.DISABLED
        self.gridA_button['state'] = tk.DISABLED
        self.gridB_button['state'] = tk.DISABLED
        self.onoff_button['state'] = tk.DISABLED
        self.one_quad["state"] = tk.DISABLED
        self.two_quad["state"] = tk.DISABLED
        self.three_quad["state"] = tk.DISABLED
        self.four_quad["state"] = tk.DISABLED

        self.lmain.destroy()
        self.my_canvas.create_image(0,0, anchor="nw", image = self.bsa_post_crop_resized_tk, state="disabled")
        
        self.draggable_roi = DrawShapes(self.my_canvas, self.quad_coords)
        self.my_canvas.bind('<Button-1>', self.draggable_roi.on_click_quad)
        
        self.my_canvas.bind('<Button1-Motion>', self.draggable_roi.on_motion)

        self.confirm_button["state"] = tk.ACTIVE

       

    #Confirms coordinates choosen 
    def confirm_roi(self):
        self.ROILocated = True
        #self.fromOverlay = True
        self.activateThresh_button['state'] = tk.ACTIVE
        
        #List of Lists containing a list for every tixel
        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]
        self.tixel_status = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]

        self.Rpoints = self.my_canvas.coords(self.draggable_roi.current)
        self.quad_coords = self.my_canvas.coords(self.draggable_roi.current)

        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.bsa_post_crop_resized_tk, state="normal")
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

        #threshold image at newly specified parameters
        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, tvalue, svalue)
        bwFile_Name = self.excelName + "BW.png"
        cv2.imwrite(bwFile_Name, thresh)
        bw = Image.open(bwFile_Name)
        sized_bw = bw.resize((self.width_post_crop_resized, self.height_post_crop_resized), Image.LANCZOS)
        bw_Image = ImageTk.PhotoImage(sized_bw)
        #checking if there is already a bw_image and replacing it if so
        if (len(self.picNames) >= 3):
            #if it is replaced with the new bw_Image
            self.picNames[2] = bw_Image
        else:
            #otherwise the new image is added to the end, which will be the 2nd index
            self.picNames.append(bw_Image)
        return bw_Image

    def grid(self, pic, id, type_img):
        #if the lmain label exists, we are coming from thresholding
        self.current_image_id = id
        if self.lmain.winfo_exists() == 1:
            self.lmain.destroy()
            self.activateThresh_button['state'] = "active"
            self.blockSize_scale['state'] = "disabled"
            self.cMean_scale['state'] = "disabled"
            
        self.value_sheFrame.set(1)
        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = pic, state="disabled")
    
        ratioNum = (self.num_chan*2) - 1
        #leftS: slope defined by the top left corner to the bottom left corner
        #[dx + point, dy + point]
        leftS = ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[6],self.Rpoints[7],ratioNum)
        #[dx + point, dy + point]
        #topS slope defined by the top left corner to the top right corner
        topS = ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[2],self.Rpoints[3],ratioNum)
        #slope: [dy, dx] for the slope defined by top left to bottom left
        slope = [round(leftS[1]-self.Rpoints[1], 5), round(leftS[0]-self.Rpoints[0], 5)]
        #slopeT: [dy, dx] for the slope defined by top left to top right
        slopeT = [round(topS[1]-self.Rpoints[1], 5), round(topS[0]-self.Rpoints[0], 5)]

        slopeO = [slope[0]*2, slope[1]*2]
        slopeTO = [slopeT[0]*2, slopeT[1]*2]
        prev = [self.Rpoints[0],self.Rpoints[1]]
        if type_img == 'quad':
            slopeO = [i/self.crop_scale_factor for i in slopeO]
            slopeTO = [i/self.crop_scale_factor for i in slopeTO]
            slope = [i/self.crop_scale_factor for i in slope]
            slopeT = [i/self.crop_scale_factor for i in slopeT]
            leftS = [i/self.crop_scale_factor for i in leftS]
            topS = [i/self.crop_scale_factor for i in topS]
            prev = [i/self.crop_scale_factor for i in prev]
        
        top = [0,0]
        left = [0,0]
        flag = False
        excelC = 1
        #each iteration on i moves the current tixel across a column
        for i in range(self.num_chan):
            top[0] = prev[0]+slopeT[1]
            top[1] = prev[1]+slopeT[0]
            flag = False
            
            #each iterations of j moves the current tixel down a row 
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
                if type_img == 'quad':
                    quad_transform_num = self.match_tixel_quad[self.current_quad_id]
                    pointer = [tL[0] + quad_transform_num[0], tL[1] + quad_transform_num[1],
                               tR[0] + quad_transform_num[0], tR[1] + quad_transform_num[1],
                               bR[0] + quad_transform_num[0], bR[1] + quad_transform_num[1],
                               bL[0] + quad_transform_num[0], bL[1] + quad_transform_num[1],
                               tL[0] + quad_transform_num[0], tL[1] + quad_transform_num[1]]
                else:
                    pointer = [tL[0],tL[1],    tR[0],tR[1],     bR[0],bR[1],   bL[0],bL[1],    tL[0],tL[1]]
                self.my_canvas.create_polygon(pointer, fill='', outline="black", tag = position, width=self.tixel_width, state="disabled")
                centerx, centery = center(tL,tR,bR,bL)
                self.coords[j][i].append(centerx/self.factor)
                self.coords[j][i].append(centery/self.factor)
                top[0] += slopeO[1]
                top[1] += slopeO[0]
                excelC += 1

                #allowing on and off tissues on overlay
                if self.classification_active:
                    if self.tixel_status[j][i] == 1:
                        try:
                            tags = self.my_canvas.find_withtag(position)
                            self.my_canvas.itemconfig(tags[0], fill='red', state="normal")
                        except IndexError:
                            self.my_canvas.itemconfig((self.num_chan*i+5)+j, fill='red', state="normal")
            prev[0] += slopeTO[1]
            prev[1] += slopeTO[0]

    #Send parameters to tissue_grid.py 
    def sendinfo(self,pic):
        self.one_quad["state"] = tk.ACTIVE
        self.two_quad["state"] = tk.ACTIVE
        self.three_quad["state"] = tk.ACTIVE
        self.four_quad["state"] = tk.ACTIVE
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
                self.my_canvas.create_polygon(pointer, fill='', outline="black", tag = position, width=self.tixel_width, state="disabled")
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
            self.tixel_status,self.spot_dia, self.fud_dia = tissue_information.theAnswer()
            for i in range(len(self.tixel_status)):
                for j in range(len(self.tixel_status)):
                    position = str(j+1) + "x" + str(i)

                    if self.tixel_status[j][i] == 1:
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
            
            ###### FIX I/J
            self.update_file["state"] = tk.ACTIVE
            if self.sendinfo_flag == False:
                with open(self.folder_selected + "/tissue_positions_list.csv") as csv_file:
                    csv_reader = csv.reader(csv_file)
                    for row in csv_reader:
                        j = int(row[2])+1
                        i = int(row[3])
                        if row[1] == "1":
                            self.tixel_status[j-1][i] = 1
                            position = str(j)+"x"+str(i)
                            try:
                                tags = self.my_canvas.find_withtag(position)
                                self.my_canvas.itemconfig(tags[0], fill='red', state="normal")
                            except IndexError:
                                pass
                        else:
                            self.tixel_status[j-1][i] = 0
                self.sendinfo_flag = True
            else:
                for i in range(len(self.tixel_status)):
                    for j in range(len(self.tixel_status)):
                        position = str(j+1) + "x" + str(i)
                        if self.tixel_status[j][i] == 1:
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
                        self.tixel_status[int(i)-1][int(j)] = 0
                    else:
                        self.my_canvas.itemconfig(k, fill="red", state ="normal", width=1)
                        self.tixel_status[int(i)-1][int(j)] = 1
                else:
                    if state == "normal":
                        self.my_canvas.itemconfig(k, state="disabled", outline="")
                        self.tixel_status[int(i)-1][int(j)] = 0
                    else:
                        self.my_canvas.itemconfig(k, state ="normal", width=1, outline="black")
                        self.tixel_status[int(i)-1][int(j)] = 1

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
                    self.tixel_status[int(i)-1][int(j)] = 1
                else:
                    self.my_canvas.itemconfig(k, width=1, state ="normal", outline="black")
                    self.tixel_status[int(i)-1][int(j)] = 1

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
                    self.tixel_status[int(i)-1][int(j)] = 0
                else:
                    self.my_canvas.itemconfig(k, state="disabled", outline="")
                    self.tixel_status[int(i)-1][int(j)] = 0

        self.my_canvas.coords("highlight", 0,0,0,0)
        self.my_canvas.unbind("<ButtonRelease-1>")
    def on_off(self, event):
        tag = event.widget.find_closest(event.x,event.y)
        # print("x: {} y: {} sf: {}".format(event.x, event.y, self.factor))
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
                self.tixel_status[int(i)-1][int(j)] = 0
                self.numTixels -= 1
            else:
                self.my_canvas.itemconfig(tag, fill="red", state ="normal", width=1)
                self.tixel_status[int(i)-1][int(j)] = 1
                self.numTixels += 1
        else:
            if state == "normal":
                self.my_canvas.itemconfig(tag, state="disabled", outline="")
                self.tixel_status[int(i)-1][int(j)] = 0
                self.numTixels -= 1
            else:
                self.my_canvas.itemconfig(tag, state ="normal", width=1, outline="black")
                self.tixel_status[int(i)-1][int(j)] = 1
                self.numTixels += 1

        


    #Creates files for spatial folder
    #Creates files for spatial folder
    def create_files(self):
        try:
            path = os.path.join(self.folder_selected, "spatial")
            os.mkdir(path)
        except FileExistsError:
            path = self.folder_selected + "/spatial"

        self.position_file["state"] = tk.DISABLED
        if self.custom_barcode_selected:
            barcodes = []
            my_file = open(self.barcode_filename,"r")
            lines = my_file.readlines()
            for line in lines:
                val = line.strip()
                barcodes.append(val)
            my_file.close()
        else:
            barcodes = []
            vals = barcode1_var.split("\n")
            for bar in vals:
                barcodes.append(bar)

        filename = path + "/tissue_positions_list.csv"
        self.write_positions_file(filename,barcodes, self.coords, self.tixel_status, 1)
        self.numTixels = 0
        for row in self.tixel_status:
            self.numTixels += sum(row)

        # print("on tixels: {}".format(self.numTixels))
# ######### FIX I/J

        # my_file.close()
        self.json_file(path)
        self.grid_button["state"] = tk.DISABLED
        self.gridA_button["state"] = tk.DISABLED
        self.gridB_button["state"] = tk.DISABLED
        self.one_quad["state"] = tk.DISABLED
        self.two_quad["state"] = tk.DISABLED
        self.three_quad["state"] = tk.DISABLED
        self.four_quad["state"] = tk.DISABLED
        try: 
            move(self.figure_folder,path)
        except shutil.Error:
            rmtree(path+"/"+"figure")
            move(self.figure_folder,path)
        # f.close()
        bwFile_Name = self.excelName + "BW.png"
        os.remove(bwFile_Name)
        mb.showinfo("Congratulations!", "The spatial folder is created!")
        

    #Creates Metadata.json
    def json_file(self,path):
        factorHigh = 0
        factorLow = 0

        print("width: {} height: {}".format(self.width_post_crop, self.height_post_crop))
        factorHigh = 2000/self.width_post_crop
        factorLow = 600/self.width_post_crop
        high_res = self.postB_cropped_pillow.resize((2000, 2000), Image.LANCZOS)
        low_res = self.postB_cropped_pillow.resize((600, 600), Image.LANCZOS)
        # if self.width_post_crop > self.height_post_crop:
        #     factorHigh = 2000/self.width_post_crop
        #     factorLow = 600/self.width_post_crop
        #     high_res = self.refactor.resize((2000, int(self.height_post_crop*factorHigh)), Image.LANCZOS)
        #     low_res = self.refactor.resize((600, int(self.height_post_crop*factorLow)), Image.LANCZOS)
        # else:
        #     factorHigh = 2000/self.height
        #     factorLow = 600/self.height
        #     high_res = self.refactor.resize((int(self.width*factorHigh), 2000), Image.LANCZOS)
        #     low_res = self.refactor.resize((int(self.width*factorLow), 600), Image.LANCZOS)

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
            ######## FIX I/J
        filepath = self.folder_selected + "/tissue_positions_list.csv"
        self.write_positions_file(filepath,barcode_lis, self.coords, self.tixel_status, self.tissue_hires_scalef)
        meta['numTixels'] = self.numTixels
        meta_json_object = json.dumps(meta, indent = 4)
        with open(self.folder_selected+ "/metadata.json", "w") as outfile:
            outfile.write(meta_json_object)
            outfile.close()
        mb.showinfo("Congratulations!", "The spatial folder has been updated!")
    
    def write_positions_file(self, filepath, barcode_lis, coordinate_lis, tixel_status_list, sf):
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            for i in range(self.num_chan):
                for j in range(self.num_chan):
                    inx = (i * self.num_chan) + j
                    writer.writerow([barcode_lis[inx].strip(), tixel_status_list[j][i], j, i, round(coordinate_lis[j][i][1] / sf), round(coordinate_lis[j][i][0] / sf)])
        f.close()

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
        ######## FIX I/J
        with open(self.folder_selected + "/tissue_positions_list_log_UMI_Genes.csv", 'r') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                j = int(row[2])+1
                i = int(row[3])
                count = float(row[which])
                position = str(j)+"x"+str(i)
                level = round((count-CBleft)/(max_value-CBleft)*50)
                cmap = matplotlib.cm.get_cmap('jet', 50)
                rgba = cmap(level)
                new = [round(i * 255) for i in rgba[:-1]]
                var = from_rgb(new)
                if self.tixel_status[j-1][i] == 1:
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
        self.cbframe.place(relx=.11, rely=.21)

        c = tk.Canvas(self.cbframe, width=220, height=50)
        c.pack()
        c.delete("all")
        for i in range(len(colorbarNorm)):
            name = "name"
            name += str(i)
            c.create_text(xvalues[i], yValue, text = str(colorbarNorm[i]), font =("Courier", 14), angle = 70, anchor = "w", tag=name)

        # colorBar
        bar = Image.open("colorbar.png")
        resized_bar = bar.resize((200, 40), Image.LANCZOS)
        color = ImageTk.PhotoImage(resized_bar)
        self.color_bar = tk.Label(self.cbframe, image=color)
        self.color_bar.pack()
        self.color_bar.image = color
        self.color_bar.configure(image=color)
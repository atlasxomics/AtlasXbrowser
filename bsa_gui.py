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
import magic
Image.MAX_IMAGE_PIXELS = None


def center(tL,tR,bR,bL):
        top = [(tL[0]+tR[0])/2,(tL[1]+tR[1])/2]
        bottom = [(bL[0]+bR[0])/2,(bL[1]+bR[1])/2]
        x = (top[0]+bottom[0])/2
        y = (top[1]+bottom[1])/2
        return x,y
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
        self.newWindow.title("Atlas Browser")
        self.newWindow.geometry("{0}x{1}".format(int(self.screen_width/1.5+290), self.screen_height))

        style = ttk.Style(root)
        root.tk.call('source', 'Azure-ttk-theme/azure/azure.tcl')
        style.theme_use('azure')

        background_image = Image.open("atlasbg.png")
        resized_image = background_image.resize((int(self.screen_width/1.5), self.screen_height), Image.ANTIALIAS)
        bg = ImageTk.PhotoImage(resized_image)

        menu = tk.Menu(self.newWindow)
        self.newWindow.config(menu=menu)
        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open Image Folder", command=self.get_folder)
        filemenu.add_command(label="Open Spatial Folder", command=self.get_spatial)
        filemenu.add_command(label="New Instance", command=self.restart)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destruct)
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
        self.check_on = tk.IntVar()
        self.check_on.set(0)
        self.quad_coords = [0]
        self.rotated_degree = 0
        self.flipped_vert = False
        self.flipped_horz = False

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

        #rotation/crop
        self.cropframe = tk.LabelFrame(self.right_canvas, text="Cropping", padx="10px", pady="10px")
        self.cropframe.place(relx=.11, rely=.01)
        self.activateCrop_button = tk.Button(self.cropframe, text = "Activate", command = self.cropping, state=tk.DISABLED)
        self.activateCrop_button.pack(side=tk.LEFT)
        self.confirmCrop_button = tk.Button(self.cropframe, text = "Confirm", command = self.square_image, state=tk.DISABLED)
        self.confirmCrop_button.pack()

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
        uparrow = Image.open("up.png")
        bg3 = ImageTk.PhotoImage(uparrow)
        self.up = tk.Button(self.rotateframe, image=bg3, command= lambda:self.image_axis(2), state=tk.DISABLED)
        self.up.image = bg3
        self.up.pack(side=tk.LEFT)
        leftarrow = Image.open("leftarrow.png")
        bg4 = ImageTk.PhotoImage(leftarrow)
        self.flip = tk.Button(self.rotateframe, image=bg4, command= lambda:self.image_axis(3), state=tk.DISABLED)
        self.flip.image = bg4
        self.flip.pack(side=tk.LEFT)
        

        #create Scales
        self.adframe = tk.LabelFrame(self.right_canvas, text="Adaptive Thresholding", padx="10px", pady="10px")
        self.adframe.place(relx=.11, rely=.23)
        self.activateThresh_button = tk.Button(self.adframe, text = "Activate", command = self.activate_thresh, state=tk.DISABLED)
        self.activateThresh_button.pack(anchor='e')
        self.blockSize_label = tk.Label(self.adframe, text="blockSize", font =("Courier", 14))
        self.blockSize_label.pack(anchor='w')

        self.blockSize_value = tk.IntVar()
        self.cMean_value = tk.IntVar()
        self.blockSize_value.set(13)
        self.cMean_value.set(11)
        self.blockSize_scale = ttk.Scale(self.adframe, variable = self.blockSize_value, from_ = 3, to = 17, orient = tk.HORIZONTAL, command= self.showThresh, length=200, state=tk.DISABLED)
        self.blockSize_scale.pack(anchor='w')
        self.cMean_label = tk.Label(self.adframe, text="Mean (to subtract)", font =("Courier", 14))
        self.cMean_label.pack(anchor='w')
        self.cMean_scale = ttk.Scale(self.adframe, variable = self.cMean_value, from_ = 0, to = 17, orient = tk.HORIZONTAL, command= self.showThresh, length=200, state=tk.DISABLED)
        self.cMean_scale.pack(anchor='w')


        #buttons
        self.thframe = tk.LabelFrame(self.right_canvas, text="Locating ROI", padx="10px", pady="10px")
        self.thframe.place(relx=.11, rely= .42)
        self.begin_button = tk.Button(self.thframe, text = "Activate", command = self.find_points, state=tk.DISABLED)
        self.begin_button.pack(side=tk.LEFT)

        self.confirm_button = tk.Button(self.thframe, text = "Confirm", command = lambda: self.confirm(None), state=tk.DISABLED)
        self.confirm_button.pack()

        self.shframe = tk.LabelFrame(self.right_canvas, text="Overlay", padx="10px", pady="10px")
        self.shframe.place(relx=.11, rely=.51)

        self.grid_button = tk.Button(self.shframe, text = "Tixels", command = lambda: self.grid(self.picNames[2]), state=tk.DISABLED)
        self.grid_button.pack(side=tk.LEFT)

        self.gridA_button = tk.Button(self.shframe, text = "BSA", command = lambda: self.grid(self.picNames[0]), state=tk.DISABLED)
        self.gridA_button.pack(anchor='w')

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

        

    def restart(self):
        self.newWindow.destroy()
        self.kill = True
        return self.kill
    def destruct(self):
        self.newWindow.destroy()


    def get_folder(self):
        self.folder_selected = filedialog.askdirectory()
        
        if self.folder_selected != '':
            temp = re.compile("/([a-zA-Z]+)([0-9]+)")
            res = temp.search(self.folder_selected).groups() 
            self.excelName = res[0]+ res[1]
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
                    try:
                        if 'image' in magic.from_file(self.folder_selected+"/"+file,mime= True):
                            self.names.append(file)
                    except IsADirectoryError:
                        pass

            self.question_window()
            
        else:
            #Add error mesage
            pass

    def get_spatial(self):
        self.folder_selected = filedialog.askdirectory()
        
        if self.folder_selected != '':
            temp = re.compile("/([a-zA-Z]+)([0-9]+)")
            res = temp.search(self.folder_selected).groups() 
            self.excelName = res[0]+ res[1]
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
                    try:
                        if 'image' in magic.from_file(self.folder_selected+"/"+file,mime= True):
                            self.names.append(file)
                    except IsADirectoryError:
                        pass

            

            try:
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
            


    def init_images(self):
        for i in self.names:
            if "bsa" in i.lower():
                beforeA = Image.open(self.figure_folder + "/" + i)
                a = beforeA
            elif "postb" in i.lower() and "bsa" not in i.lower():
                postB_Name = self.figure_folder + "/" + i
                beforeB = Image.open(postB_Name)
                b = beforeB

        w, h = (a.width, a.height)
        self.rawHeight = h
        self.width, self.height = (a.width, a.height)
        newH = self.screen_height - 60
        self.factor = newH/h
        newW = int(round(w*newH/h))
        floor = a.resize((newW, newH), Image.ANTIALIAS)
        postB = b.resize((newW, newH), Image.ANTIALIAS)

        self.refactor = b
        self.newWidth = floor.width ; self.newHeight = floor.height

        img = cv2.imread(postB_Name, cv2.IMREAD_UNCHANGED)

        flippedImage = img

        try:
            self.scale_image = cv2.cvtColor(flippedImage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedImage  

        self.imgA = ImageTk.PhotoImage(floor)
        self.imgB = ImageTk.PhotoImage(postB)
        self.picNames = [self.imgA, self.imgB]

        self.my_canvas.config(width = postB.width, height= postB.height)
        self.lmain.configure(image=self.imgB)
        self.newWindow.geometry("{0}x{1}".format(postB.width + 300, self.screen_height))
        self.right_canvas.config(width = postB.width + 300, height= h)


    def image_axis(self, num):
        if num == 0:
            updated = cv2.rotate(self.cropped_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            formatted = Image.fromarray(updated)
            sized = formatted.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(sized)
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            self.cropped_image = updated
            self.rotated_degree+=-90
        if num == 1:
            updated = cv2.rotate(self.cropped_image, cv2.ROTATE_90_CLOCKWISE)
            formatted = Image.fromarray(updated)
            sized = formatted.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(sized)
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            self.cropped_image = updated
            self.rotated_degree+=90
        if num == 2:
            updated = cv2.flip(self.cropped_image, 0)
            formatted = Image.fromarray(updated)
            sized = formatted.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(sized)
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            self.cropped_image = updated
            if self.flipped_vert == False:
                self.flipped_vert = True
            else: 
                self.flipped_vert = False
        if num == 3:
            updated = cv2.flip(self.cropped_image, 1)
            formatted = Image.fromarray(updated)
            sized = formatted.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(sized)
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            self.cropped_image = updated
            if self.flipped_horz == False:
                self.flipped_horz = True
            else: 
                self.flipped_horz = False

    def image_position(self):
        self.figure_folder = os.path.join(self.folder_selected, "figure")
        try:
            os.mkdir(self.figure_folder)
        except FileExistsError:
            rmtree(self.figure_folder)
            os.mkdir(self.figure_folder)
        self.up['state'] = tk.DISABLED
        self.left['state'] = tk.DISABLED
        self.right['state'] = tk.DISABLED
        self.flip['state'] = tk.DISABLED
        self.image_updated['state'] = tk.DISABLED
        self.activateThresh_button['state'] = tk.ACTIVE
        self.copy_images()
        self.init_images()


    def copy_images(self):
        source = self.folder_selected
        coords = self.my_canvas.coords('crop')
        for i in self.names:
            copy(source+"/"+i,self.figure_folder)

        for i in self.names:
            if "bsa" in i.lower():
                image1 = Image.open(self.figure_folder+"/"+i)   
                im1 = image1.crop((int(coords[0]/self.factor),int(coords[1]/self.factor),int(coords[2]/self.factor),int(coords[3]/self.factor)))
                bsa = im1.save(self.figure_folder+"/"+i)
            elif "postb" in i.lower() and "bsa" not in i.lower():
                image = Image.open(self.figure_folder+"/"+i)
                im2 = image.crop((int(coords[0]/self.factor),int(coords[1]/self.factor),int(coords[2]/self.factor),int(coords[3]/self.factor)))
                post = im2.save(self.figure_folder+"/"+i)
        iteration = self.rotated_degree/90
        if abs(iteration) >= 4:
            multiplier = abs(int(iteration/4))
            degree = int(abs(iteration)-(4*multiplier))
        else:
            degree = int(iteration)
        for i in self.names:
            try:
                if 'image' in magic.from_file(self.figure_folder+"/"+i,mime= True):
                    img = cv2.imread(self.figure_folder+"/"+i, cv2.IMREAD_UNCHANGED)
                    if degree < 0:
                        for x in range(abs(degree)):
                            rotate = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            img = rotate
                    elif degree > 0:
                        for y in range(abs(degree)):
                            rotate = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                            img = rotate
                    else:
                        rotate = img

                    if self.flipped_vert == True and self.flipped_horz == True:
                        once = cv2.flip(rotate,0)
                        flipped = cv2.flip(once,1)
                    elif self.flipped_horz == True and self.flipped_vert == False:
                        flipped = cv2.flip(rotate,1)
                    elif self.flipped_vert == True and self.flipped_horz == False:
                        flipped = cv2.flip(rotate,0)
                    elif self.flipped_vert == False and self.flipped_horz == False:
                        flipped = rotate

                    cv2.imwrite(self.figure_folder+"/"+i, flipped)
            except IsADirectoryError:
                pass
                
        
        

    def cropping(self):
        self.b = DrawSquare(self.my_canvas)
        self.my_canvas.bind('<Button-1>', self.b.on_click_quad)
        self.my_canvas.bind('<Button1-Motion>', self.b.on_motion)
        self.my_canvas.bind('<ButtonRelease-1>', self.b.on_release)
        self.activateCrop_button['state'] = tk.DISABLED
        self.confirmCrop_button['state'] = tk.ACTIVE


    def square_image(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<Button1-Motion>') 

        self.up['state'] = tk.ACTIVE
        self.left['state'] = tk.ACTIVE
        self.right['state'] = tk.ACTIVE
        self.flip['state'] = tk.ACTIVE
        self.image_updated['state'] = tk.ACTIVE
        self.confirmCrop_button['state'] = tk.DISABLED

        for i in self.names:
            if "postb" in i.lower() and "bsa" not in i.lower():
                beforeB = Image.open(self.postB_Name)
                b = beforeB

        w, h = (b.width, b.height)
        newH = self.screen_height - 60
        newW = int(round(w*newH/h))
        floor = b.resize((newW, newH), Image.ANTIALIAS)
        self.newWidth = floor.width ; self.newHeight = floor.height

        imgA = ImageTk.PhotoImage(floor)
        self.my_canvas.config(width = floor.width, height= floor.height)

        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        self.cropped_image = img

        self.lmain.pack()
        self.lmain.image = imgA
        self.lmain.configure(image=imgA)
        self.my_canvas.delete("image")
        self.newWindow.geometry("{0}x{1}".format(floor.width + 300, self.screen_height))
        self.right_canvas.config(width = floor.width + 300, height= h)
        
        
                

    def activate_thresh(self):
        self.blockSize_scale['state'] = tk.ACTIVE
        self.cMean_scale['state'] = tk.ACTIVE
        self.activateThresh_button['state'] = tk.DISABLED
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<B1-Motion>')
        self.my_canvas.unbind('<ButtonRelease-1>')
        
        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, self.blockSize_value.get(), self.cMean_value.get())
        bw_image = Image.fromarray(thresh)
        sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(sized_bw)
        self.lmain.image = imgtk
        self.lmain.configure(image=imgtk)
        self.begin_button['state'] = tk.ACTIVE

    def question_window(self):
        self.qWindow = tk.Toplevel(self.newWindow)
        self.qWindow.title("Meta Data")
        self.qWindow.geometry('%dx%d+%d+%d' % (400, 350, 500, 0))
        both_images_flag = 0
        for i in self.names:
            if "bsa" in i.lower():
                beforeA = Image.open(self.folder_selected + "/" + i)
                a = beforeA
                self.bsa_Name = self.folder_selected + "/" + i
                self.bar["value"] = 20
                self.pWindow.update()
                self.bar["value"] = 30
                self.pWindow.update()
                both_images_flag+=1
            elif "postb" in i.lower() and "bsa" not in i.lower():
                self.postB_Name = self.folder_selected + "/" + i
                both_images_flag+=1
        if both_images_flag==2:
            w, h = (a.width, a.height)
            newH = self.screen_height - 60
            self.factor = newH/h
            newW = int(round(w*newH/h))
            bsa = a.resize((newW, newH), Image.ANTIALIAS)
            self.qwimga = ImageTk.PhotoImage(bsa)

            self.bar["value"] = 60
            self.pWindow.update()

            temp = re.compile("/(d[0-9]+)")
            res = temp.search(self.bsa_Name.lower()).groups() 
            self.excelName = res[0].upper()
            self.newWindow.title("Atlas Browser (" + self.excelName+")")

            self.bar["value"] = 70
            self.pWindow.update()

            img = cv2.imread(self.bsa_Name, cv2.IMREAD_UNCHANGED)
            self.bar["value"] = 80
            self.pWindow.update()

            self.bar["value"] = 90
            self.pWindow.update()
            

            self.bar["value"] = 100
            self.pWindow.update()
            self.pWindow.destroy()

            
            #update canvas and frame
            self.my_canvas.config(width = bsa.width, height= bsa.height)
            self.lmain.pack_forget()
            self.my_canvas.create_image(0, 0, image=self.qwimga, anchor="nw", tag ="image")
            self.newWindow.geometry("{0}x{1}".format(bsa.width + 300, self.screen_height))
            self.right_canvas.config(width = bsa.width + 300, height= h)

            if 'metadata.json' in self.names:
                f = open(self.folder_selected + "/metadata.json")
                self.metadata = json.load(f)
                self.num_chan = int(self.metadata['numChannels'])
                os.remove(self.folder_selected + "/metadata.json")
                self.r_clicked = tk.StringVar()
                self.r_clicked.set(self.metadata['run'])
                self.s_clicked = tk.StringVar()
                self.s_clicked.set(self.metadata['species'])
                self.t_clicked = tk.StringVar()
                self.t_clicked.set(self.metadata['type'])
                self.o_clicked = tk.StringVar()
                self.o_clicked.set(self.metadata['tissue'])
                self.a_clicked = tk.StringVar()
                self.a_clicked.set(self.metadata['assay'])
                self.c_clicked = tk.StringVar()
                self.c_clicked.set(self.metadata['collaborator'])
                self.tr_clicked = tk.StringVar()
                self.tr_clicked.set(self.metadata['trimming'])
                self.n_clicked = tk.StringVar()
                self.n_clicked.set(self.metadata['numChannels'])
                

            else:
                self.r_clicked = tk.StringVar()
                self.r_clicked.set(self.excelName)
                self.s_clicked = tk.StringVar()
                self.s_clicked.set("Mouse")
                self.t_clicked = tk.StringVar()
                self.t_clicked.set("FF")
                self.o_clicked = tk.StringVar()
                self.o_clicked.set("Embryo")
                self.a_clicked = tk.StringVar()
                self.a_clicked.set("mRNA")
                self.c_clicked = tk.StringVar()
                self.c_clicked.set("Atlas")
                self.tr_clicked = tk.StringVar()
                self.tr_clicked.set("No")
                self.n_clicked = tk.StringVar()
                self.n_clicked.set(50)
                

            
            r_label = tk.Label(self.qWindow, text="Run: ", font =("Courier", 14)).place(x=20, y=10)
            r_entry = tk.Entry(self.qWindow, textvariable=self.r_clicked).place(x=200,y=10)

            s_label = tk.Label(self.qWindow, text="Species: ", font =("Courier", 14)).place(x=20, y=45)
            species = [
                "Mouse",
                "Human",
                "Rat",
                "Hamster"
            ]
            s_drop = tk.OptionMenu(self.qWindow , self.s_clicked , *species).place(x=200,y=45)

            t_label = tk.Label(self.qWindow, text="Type: ", font =("Courier", 14)).place(x=20, y=80)
            type = [
                "FF",
                "FFPE",
                "EFPE"
            ]
            t_drop = tk.OptionMenu(self.qWindow , self.t_clicked , *type).place(x=200,y=80)

            o_label = tk.Label(self.qWindow, text="Tissue: ", font=("Courier", 14)).place(x=20, y=115)
            o_entry = tk.Entry(self.qWindow, textvariable=self.o_clicked).place(x=200, y=115)

            a_label = tk.Label(self.qWindow, text="Assay: ", font =("Courier", 14)).place(x=20, y=150)
            assay = [
                "mRNA",
                "Protein",
                "ATAC",
                "H3K27me3",
                "H3K4me3",
                "H3K27ac"
            ]
            a_drop = tk.OptionMenu(self.qWindow , self.a_clicked , *assay).place(x=200,y=150)

            c_label = tk.Label(self.qWindow, text="Collaborator: ", font=("Courier", 14)).place(x=20, y=185)
            c_entry = tk.Entry(self.qWindow, textvariable=self.c_clicked).place(x=200, y=185)

            tr_label = tk.Label(self.qWindow, text="Trimming: ", font =("Courier", 14)).place(x=20, y=220)
            trim = [
                "Yes",
                "No"
            ]
            tr_drop = tk.OptionMenu(self.qWindow , self.tr_clicked , *trim).place(x=200,y=220)

            n_label = tk.Label(self.qWindow, text="Num Channels: ", font =("Courier", 14)).place(x=20, y=255)
            chan = [
                "50",
                "100"
            ]
            n_drop = tk.OptionMenu(self.qWindow , self.n_clicked , *chan).place(x=200,y=255)

            

            button = tk.Button(self.qWindow, text='Submit', font =("Courier", 14), command = self.update_meta).place(x=370, y=320, anchor=tk.SE)

        else:
            mb.showwarning("Error", "The necessary images (postB and BSA) are not present")
            self.pWindow.destroy()
        

    def update_meta(self):
        if self.r_clicked.get() == "":
            self.r_clicked.set("Test")
        self.metadata = {"run": self.r_clicked.get(),
                        "species": self.s_clicked.get(), 
                         "type": self.t_clicked.get(),
                         "tissue": self.o_clicked.get(),
                         "assay": self.a_clicked.get(),
                         "collaborator": self.c_clicked.get(),
                         "trimming": self.tr_clicked.get(),
                         "numChannels": self.n_clicked.get()}
        self.num_chan = int(self.n_clicked.get())
        self.qWindow.destroy()
        self.activateCrop_button['state'] = tk.ACTIVE
        
        
        

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

        self.newWindow.title("Atlas Browser (" + self.excelName+")")

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
        self.picNames = [None, None]  


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
        self.grid_button["state"] = tk.DISABLED
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
        

    def showThresh(self, value):
        if float(value) > 11:
            self.my_canvas.delete("all")
            sel = int(self.blockSize_value.get())
            sec = int(self.cMean_value.get())
            if sel %2 == 0:
                sel+=1
            #self.blockSize_label_value.config(text = str(sel), font =("Courier", 14))
            #self.cMean_label_value.config(text = str(sec), font =("Courier", 14))

            thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, sel, sec)
            bw_image = Image.fromarray(thresh)
            sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)
            
        else:
            self.my_canvas.delete("all")
            sel = int(self.blockSize_value.get())
            if sel %2 == 0:
                sel+=1
            sec = int(self.cMean_value.get())

            #self.blockSize_label_value.config(text = str(sel), font =("Courier", 14))
            #self.cMean_label_value.config(text = str(sec), font =("Courier", 14))

            thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, sel, sec)
            bw_image = Image.fromarray(thresh)
            sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.image = imgtk
            self.lmain.configure(image=imgtk)


    def find_points(self):
        self.blockSize_scale['state'] = tk.DISABLED
        self.cMean_scale['state'] = tk.DISABLED

        self.lmain.destroy()
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgA, state="disabled")
        
        self.c = DrawShapes(self.my_canvas, self.quad_coords)
        self.my_canvas.bind('<Button-1>', self.c.on_click_quad)
        self.my_canvas.bind('<Button1-Motion>', self.c.on_motion)

        self.confirm_button["state"] = tk.ACTIVE

    def confirm(self, none):
        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]
        tvalue = self.blockSize_value.get()
        svalue = self.cMean_value.get()
        if tvalue%2==0:
            tvalue +=1
        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, tvalue, svalue)
        bwFile_Name = self.excelName + "BW.png"
        cv2.imwrite(bwFile_Name, thresh)
        bw = Image.open(bwFile_Name)
        sized_bw = bw.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        bw_Image = ImageTk.PhotoImage(sized_bw)

        self.Rpoints = self.my_canvas.coords(self.c.current)
        self.quad_coords = self.my_canvas.coords(self.c.current)


        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgB, state="normal")
        self.my_canvas.unbind("<B1-Motion>")
        self.my_canvas.unbind("<Button-1>")
        self.picNames.append(bw_Image)
        self.confirm_button["state"] = tk.DISABLED
        self.begin_button["state"] = tk.ACTIVE
        self.grid_button["state"] = tk.ACTIVE
        self.gridA_button["state"] = tk.ACTIVE
        self.onoff_button["state"] = tk.ACTIVE
            

    def grid(self,pic):

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


    def sendinfo(self,pic):
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


        if self.picNames[0] != None:
            for child in self.labelframe.winfo_children():
                if child.winfo_class() == 'Radiobutton':
                    child['state'] = 'active'
            self.my_canvas.bind('<Button-1>',self.on_off)

            self.position_file["state"] = tk.ACTIVE
            self.begin_button['state'] = tk.DISABLED
            self.onoff_button["state"] = tk.DISABLED
            self.grid_button["state"] = tk.DISABLED
            self.gridA_button["state"] = tk.DISABLED
            
            dbit = self.excelName + "BW.png"
            points_copy = self.Rpoints.copy()
            matta = Tissue(points_copy, self.factor, dbit, self.num_chan)
            self.arr,self.spot_dia, self.fud_dia = matta.thaanswer()
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
            self.grid_button["state"] = tk.DISABLED
            self.gridA_button["state"] = tk.DISABLED
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

        



    def create_files(self):
        try:
            path = os.path.join(self.folder_selected, "spatial")
            os.mkdir(path)
        except FileExistsError:
            path = self.folder_selected + "/spatial"
        

        barcode_file = "bc"+ str(self.num_chan)+".txt"
        my_file = open(barcode_file,"r")
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
        try: 
            move(self.figure_folder,path)
        except shutil.Error:
            rmtree(path+"/"+"figure")
            move(self.figure_folder,path)
        f.close()
        bwFile_Name = self.excelName + "BW.png"
        os.remove(bwFile_Name)
        mb.showinfo("Congratulations!", "The spatial folder is created!")
        


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
                    "rawHeight": self.rawHeight}
        metaDict.update(self.metadata)
        
        json_object = json.dumps(dictionary, indent = 4)
        with open(path+"/scalefactors_json.json", "w") as outfile:
            outfile.write(json_object)
            outfile.close()
        meta_json_object = json.dumps(metaDict, indent = 4)
        with open(path+"/metadata.json", "w") as outfile:
            outfile.write(meta_json_object)
            outfile.close()

    
        
                
    def update_pos(self):
        barcode_file = "bc"+ str(self.num_chan)+".txt"
        my_file = open(barcode_file,"r")
        with open(self.folder_selected + "/tissue_positions_list.csv", 'w') as f:
            writer = csv.writer(f)
            for i in range(self.num_chan):
                for j in range(self.num_chan):
                    barcode = my_file.readline().split('\t')
                    if self.arr[j][i] == 1:
                        writer.writerow([barcode[0].strip(), 1, i, j, self.coords[j][i][1]/self.tissue_hires_scalef, self.coords[j][i][0]/self.tissue_hires_scalef])
                    else:
                        writer.writerow([barcode[0].strip(), 0, i, j, self.coords[j][i][1]/self.tissue_hires_scalef, self.coords[j][i][0]/self.tissue_hires_scalef])

              
        my_file.close()
        f.close()
        p = open(self.folder_selected + "/metadata.json")
        meta = json.load(p)
        meta['numTixels'] = self.numTixels
        meta_json_object = json.dumps(meta, indent = 4)
        with open(self.folder_selected+ "/metadata.json", "w") as outfile:
            outfile.write(meta_json_object)
            outfile.close()

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

        self.cbframe = tk.LabelFrame(self.right_canvas, text="Colorbar", padx="5px", pady="5px")
        self.cbframe.place(relx=.11, rely=.83)

        c = tk.Canvas(self.cbframe, width=220, height=40)
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
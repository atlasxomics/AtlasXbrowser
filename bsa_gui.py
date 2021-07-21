import tkinter as tk
from tkinter import ttk
import re
from tkinter.constants import DISABLED
from PIL import Image, ImageTk
import os
import csv
from draggable_quad import DrawShapes
from tkinter import filedialog
import os
import math
import json
from tissue_grid import Tissue
import cv2

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

class Gui():
    def __init__(self, root):
        self.newWindow = root
        screen_width = self.newWindow.winfo_screenwidth()
        screen_height = self.newWindow.winfo_screenheight()
        self.newWindow.title("Atlas Browser")
        self.newWindow.geometry("{0}x{1}".format(screen_width, screen_height))

        background_image = Image.open("atlasbg.png")
        resized_image = background_image.resize((int(screen_width/1.5), screen_height), Image.ANTIALIAS)
        bg = ImageTk.PhotoImage(resized_image)
        

        menu = tk.Menu(self.newWindow)
        self.newWindow.config(menu=menu)
        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open Image Folder", command=self.get_folder)
        filemenu.add_command(label="Open Spatial", command=self.get_folder)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.newWindow.quit)
        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command="")

        self.names = []
        self.num_tixels = 0
        self.folder_selected = None
        self.topx, self.topy, self.botx, self.boty = 0, 0, 0, 0
        self.points = []
        self.Rpoints = []
        self.coords = None

        #containers
        self.my_canvas = tk.Canvas(self.newWindow, width = int(screen_width/3), height= screen_height, highlightthickness = 0, bd=0)
        self.my_canvas.pack(side=tk.LEFT, anchor=tk.NW) 
        self.my_canvas.old_coords = None
        self.frame = tk.Frame(self.newWindow, width = int(screen_width/3) - screen_width, height= screen_height)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(self.frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.lmain = tk.Label(self.my_canvas)
        self.lmain.pack()
        self.lmain.img = bg
        self.lmain.configure(image=bg)
        

        #create Scales
        self.thresh_label = tk.Label(self.frame, text="Threshold Value Scale", font =("Courier", 14))
        self.thresh_label.place(x=17,y=10)
        self.thresh_label_value = tk.Label(self.frame, text="255")
        self.thresh_label_value.place(x=17,y=60)
        self.spot_label = tk.Label(self.frame, text="SpotRemover Value Scale", font =("Courier", 14))
        self.spot_label.place(x=17,y=80)
        self.spot_label_value = tk.Label(self.frame, text="17")
        self.spot_label_value.place(x=17,y=130)

        self.thresh_value = tk.IntVar()
        self.spot_value = tk.IntVar()
        self.thresh_value.set(255)
        self.spot_value.set(17)
        self.thresh_scale = ttk.Scale(self.frame, variable = self.thresh_value, from_ = 19, to = 255, orient = tk.HORIZONTAL, command= self.showThresh)  
        self.thresh_scale.place(x=17,y=40, relwidth=.8)
        self.spot_scale = ttk.Scale(self.frame, variable = self.spot_value, from_ = 0, to = 17, orient = tk.HORIZONTAL, command= self.showThresh)  
        self.spot_scale.place(x=17,y=110, relwidth=.8)


        #buttons

        self.begin_button = tk.Button(self.frame, text = "Place Markers", command = self.find_points, state=tk.ACTIVE)
        self.begin_button.place(relx=.3, y= 200)

        self.confirm_button = tk.Button(self.frame, text = "Confirm", command = lambda: self.confirm(None), state=tk.DISABLED)
        self.confirm_button.place(relx=.3, y= 230)

        self.roi_button = tk.Button(self.frame, text = "Show Roi", command = self.roi, state=tk.DISABLED)
        self.roi_button.place(relx=.1, y= 260)

        self.grid_button = tk.Button(self.frame, text = "Show Grid", command = lambda: self.grid(self.picNames[2]), state=tk.DISABLED)
        self.grid_button.place(relx=.3, y= 260)

        self.gridA_button = tk.Button(self.frame, text = "Show Grid on PostB", command = lambda: self.grid(self.picNames[0]), state=tk.DISABLED)
        self.gridA_button.place(relx=.5, y= 260)

        self.onoff_button = tk.Button(self.frame, text = "On/Off Tissue", command = lambda: self.sendinfo(self.picNames[2]), state=tk.DISABLED)
        self.onoff_button.place(relx=.1, y= 290)

        self.labelframe = tk.LabelFrame(self.frame, text="Selection Tools")
        self.labelframe.place(relx=.5, y= 290)
        self.value_labelFrame = tk.IntVar()
        self.value_labelFrame.set(1)
        tk.Radiobutton(self.labelframe, text="One by One", variable=self.value_labelFrame, value=1, command = self.offon).pack()
        tk.Radiobutton(self.labelframe, text="Highlight", variable=self.value_labelFrame, value=2, command = self.highlit).pack()
        for child in self.labelframe.winfo_children():
            if child.winfo_class() == 'Radiobutton':
                child['state'] = 'disabled'

        self.position_file = tk.Button(self.frame, text = "Create Spatial Folder", command = self.create_files, state=tk.DISABLED)
        self.position_file.place(relx=.1, y= 350)



    def get_folder(self):
        self.folder_selected = filedialog.askdirectory()
        for file in os.listdir(self.folder_selected):
            if file.startswith(".") == False:
                self.names.append(file)

        if "spatial" not in self.folder_selected:
            self.init_images()
            self.question_window()

        else:
            f = open(self.folder_selected + "/metadata.json")
            self.metadata = json.load(f)
            self.num_chan = int(self.metadata['numChannels'])
            self.second_window()
            

        

    def init_images(self):
        for i in self.names:
            if "BSA" in i:
                beforeA = Image.open(self.folder_selected + "/" + i)
                a = beforeA.transpose(Image.FLIP_LEFT_RIGHT)
            elif "postB" in i:
                self.postB_Name = self.folder_selected + "/" + i
                beforeB = Image.open(self.postB_Name)
                b = beforeB.transpose(Image.FLIP_LEFT_RIGHT)


        w, h = (a.width, a.height)
        self.width, self.height = (a.width, a.height)
        if h > 850:
            self.factor = 850/h
            newW = int(round(w*850.0/h))
            floor = a.resize((newW, 850), Image.ANTIALIAS)
            postB = b.resize((newW, 850), Image.ANTIALIAS)
        else:
            floor = a
            postB = b
            self.factor = 1

        self.refactor = b
        self.newWidth = floor.width ; self.newHeight = floor.height
        temp = re.compile("/([a-zA-Z]+)([0-9]+)_postB")
        res = temp.search(self.postB_Name).groups() 
        self.excelName = res[0]+ res[1]
        
        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        flippedimage = cv2.flip(img, 1)
        try:
            self.scale_image = cv2.cvtColor(flippedimage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedimage   

        self.imgA = ImageTk.PhotoImage(floor)
        self.imgB = ImageTk.PhotoImage(postB)
        self.picNames = [self.imgA, self.imgB]  


        #update canvas and frame
        self.my_canvas.config(width = floor.width, height= floor.height)
        self.lmain.configure(image=self.imgA)
        self.frame.config(width = floor.width-w, height= h)
        

    def question_window(self):
        self.qWindow = tk.Toplevel(self.newWindow)
        self.qWindow.title("Meta Data")
        self.qWindow.geometry("400x300")

        if 'metadata.json' in self.names:
            f = open(self.folder_selected + "/metadata.json")
            self.metadata = json.load(f)
            self.num_chan = int(self.metadata['numChannels'])
            os.remove(self.folder_selected + "/metadata.json")
            self.s_clicked = tk.StringVar()
            self.s_clicked.set(self.metadata['species'])
            self.t_clicked = tk.StringVar()
            self.t_clicked.set(self.metadata['type'])
            self.tr_clicked = tk.StringVar()
            self.tr_clicked.set(self.metadata['trimming'])
            self.a_clicked = tk.StringVar()
            self.a_clicked.set(self.metadata['assay'])
            self.n_clicked = tk.StringVar()
            self.n_clicked.set(self.metadata['numChannels'])

        else:
            self.s_clicked = tk.StringVar()
            self.s_clicked.set("Mouse")
            self.t_clicked = tk.StringVar()
            self.t_clicked.set("FF")
            self.tr_clicked = tk.StringVar()
            self.tr_clicked.set("Yes")
            self.a_clicked = tk.StringVar()
            self.a_clicked.set("mRNA")
            self.n_clicked = tk.StringVar()
            self.n_clicked.set(50)

        s_label = tk.Label(self.qWindow, text="Species: ", font =("Courier", 14)).place(x=20, y=10)
        species = [
            "Mouse",
            "Human"
        ]
        s_drop = tk.OptionMenu(self.qWindow , self.s_clicked , *species).place(x=200,y=10)

        t_label = tk.Label(self.qWindow, text="Type: ", font =("Courier", 14)).place(x=20, y=45)
        type = [
            "FF",
            "FFPE"
        ]
        t_drop = tk.OptionMenu(self.qWindow , self.t_clicked , *type).place(x=200,y=45)

        tr_label = tk.Label(self.qWindow, text="Trimming: ", font =("Courier", 14)).place(x=20, y=80)
        trim = [
            "Yes",
            "No"
        ]
        tr_drop = tk.OptionMenu(self.qWindow , self.tr_clicked , *trim).place(x=200,y=80)

        a_label = tk.Label(self.qWindow, text="Assay: ", font =("Courier", 14)).place(x=20, y=115)
        assay = [
            "mRNA",
            "Protein",
            "Epigenome"
        ]
        a_drop = tk.OptionMenu(self.qWindow , self.a_clicked , *assay).place(x=200,y=115)

        n_label = tk.Label(self.qWindow, text="Num Channels: ", font =("Courier", 14)).place(x=20, y=150)
        chan = [
            "50",
            "100"
        ]
        n_drop = tk.OptionMenu(self.qWindow , self.n_clicked , *chan).place(x=200,y=150)

        button = tk.Button(self.qWindow, text='Submit', font =("Courier", 14), command = self.update_meta).place(x=350, y=250, anchor=tk.SE)
        
        

    def update_meta(self):
        self.metadata = {"species": self.s_clicked.get(), 
                         "type": self.t_clicked.get(), 
                         "trimming": self.tr_clicked.get(), 
                         "assay": self.a_clicked.get(), 
                         "numChannels": self.n_clicked.get()}
        self.num_chan = int(self.n_clicked.get())
        self.qWindow.destroy()

    def second_window(self):
        for i in self.names:
            if "meta" in i:
                self.json = self.folder_selected + "/" + i

            elif "list" in i:
                self.position = self.folder_selected + "/" + i


        temp = re.compile("/([a-zA-Z]+)([0-9]+).image")
        res = temp.search(self.folder_selected).groups() 
        self.excelName = res[0]+ res[1]

        previous = self.folder_selected[: len(self.folder_selected)-7]
        self.postB_Name = previous + self.excelName + "_postB.png"
        beforeB = Image.open(self.postB_Name)
        a = beforeB.transpose(Image.FLIP_LEFT_RIGHT)


        w, h = (a.width, a.height)
        self.width, self.height = (a.width, a.height)
        if h > 850:
            self.factor = 850/h
            newW = int(round(w*850.0/h))
            floor = a.resize((newW, 850), Image.ANTIALIAS)
        else:
            floor = a
            self.factor = 1

        self.refactor = a
        self.newWidth = floor.width ; self.newHeight = floor.height
        
        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        flippedimage = cv2.flip(img, 1)
        try:
            self.scale_image = cv2.cvtColor(flippedimage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedimage   

        self.imgA = ImageTk.PhotoImage(floor)
        self.picNames = [None, None]  


        #update canvas and frame
        self.my_canvas.config(width = floor.width, height= floor.height)
        self.lmain.destroy()
        self.frame.config(width = floor.width-w, height= h)
        self.Rpoints = self.metadata['points']
        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]
        self.arr = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]

        #Buttons
        self.begin_button['state'] = tk.DISABLED
        self.confirm_button['state'] = tk.DISABLED
        self.thresh_scale['state'] = tk.DISABLED
        self.spot_scale['state'] = tk.DISABLED
        self.roi_button["state"] = tk.DISABLED
        self.grid_button["state"] = tk.ACTIVE
        self.onoff_button["state"] = tk.ACTIVE
        self.update_file = tk.Button(self.frame, text = "Update Position File", command = self.update_pos)
        self.update_file.place(relx=.1, y= 380)


        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, int(self.metadata['th1']), int(self.metadata['th2']))
        bw_image = Image.fromarray(thresh)
        sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(sized_bw)
        self.picNames.append(imgtk)
        self.my_canvas.create_image(0,0, anchor="nw", image = imgtk, state="disabled")

        

    def showThresh(self, value):
        if float(value) > 11:
            self.my_canvas.delete("all")
            sel = int(self.thresh_value.get())
            if sel %2 == 0:
                sel+=1
            sec = int(self.spot_value.get())

            self.thresh_label_value.config(text = str(sel), font =("Courier", 14))
            self.spot_label_value.config(text = str(sec), font =("Courier", 14))

            thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, sel, sec)
            bw_image = Image.fromarray(thresh)
            sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.imgtk = imgtk
            self.lmain.configure(image=imgtk)
            
        else:
            self.my_canvas.delete("all")
            sel = int(self.thresh_value.get())
            if sel %2 == 0:
                sel+=1
            sec = int(self.spot_value.get())

            self.thresh_label_value.config(text = str(sel), font =("Courier", 14))
            self.spot_label_value.config(text = str(sec), font =("Courier", 14))

            thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, sel, sec)
            bw_image = Image.fromarray(thresh)
            sized_bw = bw_image.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=sized_bw) 
            self.lmain.imgtk = imgtk
            self.lmain.configure(image=imgtk)


    def find_points(self):
        self.thresh_scale['state'] = tk.DISABLED
        self.spot_scale['state'] = tk.DISABLED

        self.lmain.destroy()
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgA, state="disabled")
        
        self.c = DrawShapes(self.my_canvas)
        self.my_canvas.bind('<Button-1>', self.c.on_click_quad)
        self.my_canvas.bind('<Button1-Motion>', self.c.on_motion)

        self.confirm_button["state"] = tk.ACTIVE

    def confirm(self, none):
        self.coords = [[[] for i in range(self.num_chan)] for i in range(self.num_chan)]
        tvalue = self.thresh_value.get()
        svalue = self.spot_value.get()
        if tvalue%2==0:
            tvalue +=1
        thresh = cv2.adaptiveThreshold(self.scale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, tvalue, svalue)
        bwFile_Name = self.excelName + "BW.png"
        cv2.imwrite(bwFile_Name, thresh)
        bw = Image.open(bwFile_Name)
        sized_bw = bw.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        bw_Image = ImageTk.PhotoImage(sized_bw)

        self.Rpoints = self.my_canvas.coords(self.c.current)

        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgB, state="normal")
        self.my_canvas.unbind("<B1-Motion>")
        self.my_canvas.unbind("<Button-1>")
        self.picNames.append(bw_Image)
        self.confirm_button["state"] = tk.DISABLED
        self.begin_button["state"] = tk.DISABLED
        self.roi_button["state"] = tk.ACTIVE
        self.grid_button["state"] = tk.ACTIVE
        self.gridA_button["state"] = tk.ACTIVE
        self.onoff_button["state"] = tk.ACTIVE
            
            


    def roi(self):
        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgB)
        self.my_canvas.create_polygon(self.Rpoints, fill ="",outline="black", tags="roi")

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
            self.onoff_button["state"] = tk.DISABLED
            self.roi_button["state"] = tk.DISABLED
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
            self.my_canvas.bind('<Button-1>',self.on_off)

            self.update_file["state"] = tk.ACTIVE
            self.onoff_button["state"] = tk.DISABLED
            self.roi_button["state"] = tk.DISABLED
            self.grid_button["state"] = tk.DISABLED
            self.gridA_button["state"] = tk.DISABLED

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
                if state == "normal":
                    self.my_canvas.itemconfig(k, fill="", state="disabled")
                    self.arr[int(i)][int(j)] = 0
                else:
                    self.my_canvas.itemconfig(k, fill="red", state ="normal")
                    self.arr[int(i)][int(j)] = 1
        self.my_canvas.coords("highlight", 0,0,0,0)
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
        if state ==  "normal":
            self.my_canvas.itemconfig(tag, fill="", state="disabled")
            self.arr[int(i)][int(j)] = 0
        else:
            self.my_canvas.itemconfig(tag, fill="red", state ="normal")
            self.arr[int(i)][int(j)] = 1
        



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

            for i in range(self.num_chan):
                for j in range(self.num_chan):
                    barcode = my_file.readline().split('\t')
                    if self.arr[j][i] == 1:
                        self.num_tixels+=1
                        writer.writerow([barcode[0].strip(), 1, i, j, self.coords[j][i][1], self.coords[j][i][0]])
                    else:
                        writer.writerow([barcode[0].strip(), 0, i, j, self.coords[j][i][1], self.coords[j][i][0]])

                excelC += 1
              
        my_file.close()
        self.json_file(path)
        f.close()

    def json_file(self,path):
        factorHigh = 0
        factorLow = 0

        if self.width > self.height:
            factorHigh = 2000/self.width
            factorLow = 600/self.width
            high_res = self.refactor.resize((2000, int(self.height*factorHigh)), Image.ANTIALIAS)
            low_res = self.refactor.resize((600, int(self.height*factorLow)), Image.ANTIALIAS)
            high_res.save(path+"/tissue_hires_image.png")
            low_res.save(path+"/tissue_lowres_image.png")
        if self.height > self.width:
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
        sel = int(self.thresh_value.get())
        if sel %2 == 0:
            sel+=1
        sec = int(self.spot_value.get())
        metaDict = {"points" : self.Rpoints,
                    "th1": sel,
                    "th2": sec,
                    "num_tixels": self.num_tixels}
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
        excelC = 1
        with open(self.folder_selected + "/tissue_positions_list.csv", 'w') as f:
            writer = csv.writer(f)
            for i in range(self.num_chan):
                for j in range(self.num_chan):
                    barcode = my_file.readline().split('\t')
                    if self.arr[j][i] == 1:
                        writer.writerow([barcode[0].strip(), 1, i, j, self.coords[j][i][1], self.coords[j][i][0]])
                    else:
                        writer.writerow([barcode[0].strip(), 0, i, j, self.coords[j][i][1], self.coords[j][i][0]])

                excelC += 1
              
        my_file.close()
        f.close()


    
        

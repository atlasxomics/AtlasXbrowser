import tkinter as tk
import re
from PIL import Image, ImageTk
import os
import xlsxwriter as excel
import csv
from mouse_mover import MouseMover
from tkinter import ttk
from tkinter import filedialog
import os
import math
import json
from tissue_grid import Tissue
import cv2


class Gui():
    def __init__(self, root):
        self.root = root
        self.root.title("GUI")
        self.root.geometry("500x200")
        btn = tk.Button(self.root, text ="Start", command = self.second_window)
        btn.grid(row=2, column=2)
        self.folderPath = tk.StringVar()
        a = tk.Label(self.root ,text="Enter name")
        a.grid(row=0,column = 0)
        E = tk.Entry(self.root,textvariable=self.folderPath)
        E.grid(row=0,column=1)
        btnFind = ttk.Button(self.root, text="Browse Folder",command=self.getFolderPath)
        btnFind.grid(row=0,column=2)
        self.names = []
        self.folderPath = tk.StringVar()
        a = tk.Label(self.root ,text="Enter name")
        a.grid(row=0,column = 0)
        E = tk.Entry(self.root,textvariable=self.folderPath)
        E.grid(row=0,column=1)
        btnFind = ttk.Button(self.root, text="Browse Folder",command= self.getFolderPath)
        btnFind.grid(row=0,column=2)
        self.names = []

    def second_window(self):
        self.arr = None
        self.total_pixels = None
        self.topx, self.topy, self.botx, self.boty = 0, 0, 0, 0

        self.newWindow = tk.Toplevel(self.root)
        screen_width = self.newWindow.winfo_screenwidth()
        screen_height = self.newWindow.winfo_screenheight()
        self.newWindow.title("Bioinformatics")
        self.newWindow.geometry("{0}x{1}".format(screen_width, screen_height))


        for i in self.names:
            if "BSA" in i:
                beforeA = Image.open(self.folderPath.get() + "/" + i)
                a = beforeA.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                self.postB_Name = self.folderPath.get() + "/" + i
                beforeB = Image.open(self.postB_Name)
                b = beforeB.transpose(Image.FLIP_LEFT_RIGHT)

        

        w, h = (a.width, a.height)
        self.width, self.height = (a.width, a.height)
        if w > 1200 and h > 850:
            self.factorW = 1200/w
            self.factorH = 850/h
            floor = a.resize((1200, 850), Image.ANTIALIAS)
            postB = b.resize((1200, 850), Image.ANTIALIAS)
        elif w > 1200:
            self.factorW = 1200/w
            self.factorH = 1
            floor = a.resize((1200, h), Image.ANTIALIAS)
            postB = b.resize((1200, h), Image.ANTIALIAS)
        elif h > 850:
            floor = a.resize((w, 850), Image.ANTIALIAS)
            postB = b.resize((w, 850), Image.ANTIALIAS)
            self.factorH = 850/h
            self.factorW = 1
        else:
            floor = a
            postB = b
            self.factorW = 1
            self.factorH = 1

        self.refactor = b
        self.newWidth = floor.width ; self.newHeight = floor.height
        temp = re.compile("([a-zA-Z]+)([0-9]+)")
        res = temp.match(self.names[0]).groups() 
        self.excelName = res[0]+ res[1]
        
        #These is where you need to change
        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        flippedimage = cv2.flip(img, 1)
        try:
            gray = cv2.cvtColor(flippedimage, cv2.COLOR_BGR2GRAY)
            #change the below line of code to thresh you want
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 135, 7)
        except cv2.error:
            #use the same number here
            thresh = cv2.adaptiveThreshold(flippedimage, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 135, 7)
            
        bwFile_Name = self.excelName + "BW.png"
        cv2.imwrite(bwFile_Name, thresh)
        bw = Image.open(bwFile_Name)
        sized_bw = bw.resize((self.newWidth, self.newHeight), Image.ANTIALIAS)
        self.bw_Image = ImageTk.PhotoImage(sized_bw)

        #containers
        self.my_canvas = tk.Canvas(self.newWindow, width = floor.width, height= floor.height, highlightthickness = 0, bd=0)
        self.my_canvas.pack(side=tk.LEFT, anchor=tk.NW) 
        frame = tk.Frame(self.newWindow, width = floor.width-w, height= h)
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.BOTH)


        #images
        self.imgA = ImageTk.PhotoImage(floor)
        self.createdA = self.my_canvas.create_image(0,0, anchor='nw', image = self.imgA, state="disabled")
        self.imgB = ImageTk.PhotoImage(postB)
        picNames = [self.bw_Image,self.imgB]

        #tk.Label for Coord of ROI
        self.topLeft = tk.StringVar(); self.topLeft.set("TopLeft: x,y")
        self.topRight = tk.StringVar(); self.topRight.set("TopRight: x,y")
        self.bottomLeft = tk.StringVar(); self.bottomLeft.set("BottomLeft: x,y")
        self.bottomRight = tk.StringVar(); self.bottomRight.set("BottomRight: x,y")

        labelframe_widget = tk.LabelFrame(frame, text="Coords of ROI")
        labelframe_widget.place(x=0, y=20, height=220, relwidth=.8)

        label_widgetTL = tk.Label(labelframe_widget, textvariable= self.topLeft)
        label_widgetTL.place(x=0,y=10)
        label_widgetTR = tk.Label(labelframe_widget, textvariable= self.topRight)
        label_widgetTR.place(x=0,y=60)
        label_widgetBL = tk.Label(labelframe_widget, textvariable= self.bottomLeft)
        label_widgetBL.place(x=0,y=110)
        label_widgetBR = tk.Label(labelframe_widget, textvariable= self.bottomRight)
        label_widgetBR.place(x=0,y=160)


        #buttons
        self.begin_button = tk.Button(frame, text = "Begin", command = self.find_points, state=tk.ACTIVE)
        self.begin_button.place(x=0, y= screen_height-300)

        self.confirm_button = tk.Button(frame, text = "Confirm", command = self.confirm, state=tk.DISABLED)
        self.confirm_button.place(x=0, y= screen_height-273)

        self.roi_button = tk.Button(frame, text = "Show Roi", command = self.roi, state=tk.DISABLED)
        self.roi_button.place(x=0, y= screen_height-246)

        self.grid_button = tk.Button(frame, text = "Show Grid", command = lambda: self.grid(picNames[0]), state=tk.DISABLED)
        self.grid_button.place(x=0, y= screen_height-219)

        self.gridA_button = tk.Button(frame, text = "Show Grid on PostB", command = lambda: self.grid(picNames[1]), state=tk.DISABLED)
        self.gridA_button.place(x=0, y= screen_height-192)

        self.onoff_button = tk.Button(frame, text = "On Off", command = self.sendinfo, state=tk.DISABLED)
        self.onoff_button.place(x=100, y=screen_height-300)

        self.position_file = tk.Button(frame, text = "Create Position File", command = self.create_files, state=tk.DISABLED)
        self.position_file.place(x=100, y=screen_height-400)

        self.Rpoints = []
        self.it = 0
        self.coords = [[[] for i in range(50)] for i in range(50)]
        

        #excel Sheet creation
        path = os.path.join(self.folderPath.get(), "spatial")
        os.mkdir(path)
        




    def getFolderPath(self):
        folder_selected = filedialog.askdirectory()
        for file in os.listdir(folder_selected):
            if file.startswith(".") == False:
                self.names.append(file)
        self.folderPath.set(folder_selected)

    def json_file(self):
        factorHigh = 0
        factorLow = 0
        path = os.path.join(self.folderPath.get(), "spatial")
        

        if self.width > self.height:
            factorHigh = 2000/self.width
            factorLow = 600/self.width
            high_res = self.refactor.resize((2000, int(self.height*factorHigh)), Image.ANTIALIAS)
            low_res = self.refactor.resize((600, int(self.height*factorLow)), Image.ANTIALIAS)
            high_res.save(path+"/tissue_hires_image.png")
            low_res.save(path+"/tissue_lores_image.png")
        if self.height > self.width:
            factorHigh = 2000/self.height
            factorLow = 600/self.height
            high_res = self.refactor.resize((int(self.width*factorHigh), 2000), Image.ANTIALIAS)
            low_res = self.refactor.resize((int(self.width*factorLow), 600), Image.ANTIALIAS)
            high_res.save(path+"/tissue_hires_image.png")
            low_res.save(path+"/tissue_lores_image.png")
        
        dictionary = {"spot_diameter_fullres": self.total_pixels, 
                        "tissue_hires_scalef": factorHigh, 
                        "fiducial_diameter_fullres": 1, 
                        "tissue_lowres_scalef": factorLow}
        
        json_object = json.dumps(dictionary)
        with open(path+"/scalefactors_json.json", "w") as outfile:
            outfile.write(json_object)
            outfile.close()
        
        
    def ratio50l(self, xc,yc,xr,yr,a):
        txp = xc + (a/(99))*(xr-xc)
        typ = yc + (a/(99))*(yr-yc)
        return [txp , typ]

    def find_points(self):
        self.it += 1
        
        mm = MouseMover(self.my_canvas)
        self.my_canvas.bind("<Button-1>", mm.find_object)
        self.my_canvas.bind("<B1-Motion>", mm.drag)
        
        self.my_canvas.create_polygon(10,10,  20,10,  20,20, 10,20,  10,10,fill="", outline="blue", width=1, tags="point"+str(self.it)+"1")
        self.my_canvas.create_polygon(self.my_canvas.winfo_width()-20,10, self.my_canvas.winfo_width()-10,10,self.my_canvas.winfo_width()-10,20,self.my_canvas.winfo_width()-20,20,self.my_canvas.winfo_width()-20,10, fill="", outline="blue", width=1, tags="point"+str(self.it)+"2")
        self.my_canvas.create_polygon(10,self.my_canvas.winfo_height()-20, 20,self.my_canvas.winfo_height()-20,  20,self.my_canvas.winfo_height()-10, 10,self.my_canvas.winfo_height()-10, 10,self.my_canvas.winfo_height()-20, fill="", outline="blue", width=1, tags="point"+str(self.it)+"3")
        self.my_canvas.create_polygon(self.my_canvas.winfo_width()-20,self.my_canvas.winfo_height()-20,  self.my_canvas.winfo_width()-10,self.my_canvas.winfo_height()- 20,   self.my_canvas.winfo_width()-10,self.my_canvas.winfo_height()- 10,  self.my_canvas.winfo_width()-20,self.my_canvas.winfo_height()-10,  self.my_canvas.winfo_width()-20,self.my_canvas.winfo_height()-10, fill="", outline="blue", width=1, tags="point"+str(self.it)+"4")

        self.confirm_button["state"] = tk.ACTIVE
        

    def get_mouse_posn(self, event):
        self.my_canvas.unbind("<ButtonRelease-1>")
        self.topx, self.topy = event.x, event.y
        self.my_canvas.create_rectangle(self.topx, self.topy, self.topx, self.topy,dash=(2,2), fill='', tag= "highlight", outline='black')

    def release(self,event):
        for i in self.my_canvas.find_overlapping(self.topx, self.topy, self.botx, self.boty):
            position = event.widget.gettags(i)
            if len(position) > 0 and position[0]!="highlight":
                where = position[0].split("x")
                state = self.my_canvas.itemcget(i,'state')
                if state ==  "normal":
                    self.my_canvas.itemconfig(i, fill="", stipple="", state="disabled")
                    i = where[0]
                    j = where[1]
                    self.arr[int(i)][int(j)] = 0
                    
                else:
                    self.my_canvas.itemconfig(i, fill="green", stipple="gray50", state ="normal")
                    i = where[0]
                    j = where[1]
                    self.arr[int(i)][int(j)] = 1
        self.my_canvas.coords("highlight", 0,0,0,0)

    def update_sel_rect(self, event):
        self.my_canvas.bind("<ButtonRelease-1>", self.release)
        self.botx, self.boty = event.x, event.y
        self.my_canvas.coords("highlight", self.topx, self.topy, self.botx, self.boty)  # Update selection rect.
        

    def on_off(self,event):
        tag = event.widget.find_closest(event.x,event.y)
        position = event.widget.gettags(tag)
        print(position)
        where = position[0].split("x")
        state = self.my_canvas.itemcget(tag,'state')
        if state ==  "normal":
            self.my_canvas.itemconfig(tag, fill="", stipple="", state="disabled")
            i = where[0]
            j = where[1]
            self.arr[int(i)][int(j)] = 0
            
        else:
            self.my_canvas.itemconfig(tag, fill="green", stipple="gray50", state ="normal")
            i = where[0]
            j = where[1]
            self.arr[int(i)][int(j)] = 1
        
    def create_files(self):
        my_file = open("barcode.txt","r")
        excelC = 1
        self.csv_file = [0,0,0,0,0,0]
        path = os.path.join(self.folderPath.get(), "spatial")
        with open(path + "/tissue_position_list.csv", 'w') as f:
            writer = csv.writer(f)


            for i in range(50):
                for j in range(50):
                    self.csv_file = [0,0,0,0,0,0]
                    barcode = my_file.readline().split('\t')
                    self.csv_file[0] = barcode[0]
                    if self.arr[j][i] == 1:
                        self.csv_file[1] = 1
                    else:
                        self.csv_file[1] = 0

                    self.csv_file[2] = j
                    self.csv_file[3] = i
                    self.csv_file[4] = self.coords[j][i][0]
                    self.csv_file[5] = self.coords[j][i][1]
                    
                
                    writer.writerow(self.csv_file) 
                excelC += 1
              
        my_file.close()
        self.json_file()
        f.close()
                
                
    def confirm(self):
        sorter = []

        oval1 = self.my_canvas.coords("point11")
        oval2 = self.my_canvas.coords("point12")
        oval3 = self.my_canvas.coords("point13")
        oval4 = self.my_canvas.coords("point14")

        sorter.append(oval1), sorter.append(oval2),sorter.append(oval3),sorter.append(oval4)
        smallX = sorted(sorter , key=lambda x: x[0] )
        leftSide = sorted(smallX[:2], key=lambda x: x[1])
        rightSide = sorted(smallX[2:], key=lambda x: x[1])

        tL = [leftSide[0][0], leftSide[0][1]]
        bL = [leftSide[1][6], leftSide[1][7]]
        tR = [rightSide[0][2], rightSide[0][3]]
        bR = [rightSide[1][4], rightSide[1][5]]    

        self.Rpoints.append(tL[0]);self.Rpoints.append(tL[1])
        self.Rpoints.append(tR[0]);self.Rpoints.append(tR[1])
        self.Rpoints.append(bR[0]);self.Rpoints.append(bR[1])
        self.Rpoints.append(bL[0]);self.Rpoints.append(bL[1])

        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgB, state="normal")
        self.my_canvas.unbind("<B1-Motion>")
        self.my_canvas.unbind("<Button-1>")
        self.confirm_button["state"] = tk.DISABLED
        self.begin_button["state"] = tk.DISABLED
        self.roi_button["state"] = tk.ACTIVE
        self.grid_button["state"] = tk.ACTIVE
        self.gridA_button["state"] = tk.ACTIVE
        self.onoff_button["state"] = tk.ACTIVE
        self.position_file["state"] = tk.ACTIVE

    
    def roi(self):
        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgB)
        self.my_canvas.create_polygon(self.Rpoints, fill ="",outline="black", tags="roi")

    def grid(self,pic):
        self.my_canvas.delete("all")
        self.grid_image = self.my_canvas.create_image(0,0, anchor="nw", image = pic, state="disabled")

        leftS = self.ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[6],self.Rpoints[7],1)
        topS = self.ratio50l(self.Rpoints[0],self.Rpoints[1],self.Rpoints[2],self.Rpoints[3],1)
        slope = [round(leftS[1]-self.Rpoints[1], 5), round(leftS[0]-self.Rpoints[0], 5)]
        slopeT = [round(topS[1]-self.Rpoints[1], 5), round(topS[0]-self.Rpoints[0], 5)]


        slopeO = [slope[0]*2, slope[1]*2]
        slopeTO = [slopeT[0]*2, slopeT[1]*2]
        
        top = [0,0]
        left = [0,0]
        flag = False
        prev = [self.Rpoints[0],self.Rpoints[1]]
        excelC = 1
        for i in range(50):
            top[0] = prev[0]+slopeT[1]
            top[1] = prev[1]+slopeT[0]
            flag = False
            
            for j in range(50):
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
                position = "{0}x{1}".format(str(j),str(i))
                pointer = [tL[0],tL[1],    tR[0],tR[1],     bR[0],bR[1],   bL[0],bL[1],    tL[0],tL[1]]
                self.my_canvas.create_polygon(pointer, fill='', outline="black", tag = position, width=1, state="disabled")
                centerx, centery = self.center(tL,tR,bR,bL)
                self.coords[j][i].append(centerx/self.factorW)
                self.coords[j][i].append(centery/self.factorH)
                top[0] += slopeO[1]
                top[1] += slopeO[0]
                excelC += 1
            prev[0] += slopeTO[1]
            prev[1] += slopeTO[0]
            

            

    def sendinfo(self):
        #self.my_canvas.bind("<Button-1>", self.on_off)
        self.my_canvas.bind('<Button-1>', self.get_mouse_posn)
        self.my_canvas.bind('<B1-Motion>', self.update_sel_rect)
        self.my_canvas.bind('<ButtonRelease-1>', self.release)
        dbit = self.excelName + "BW.png"
        matta = Tissue(self.Rpoints, self.factorW, self.factorH, dbit, self.excelName)
        self.arr,self.total_pixels = matta.thaanswer()
        for i in range(len(self.arr)):
            for j in range(len(self.arr)):
                position = str(j) + "x" + str(i)
                if self.arr[j][i] == 1:
                    try:
                        self.my_canvas.itemconfig(position, fill='green', stipple="gray50", state = "normal")
                    except tk.TclError:
                        pass
        

    def center(self,tL,tR,bR,bL):
        top = [(tL[0]+tR[0])/2,(tL[1]+tR[1])/2]
        bottom = [(bL[0]+bR[0])/2,(bL[1]+bR[1])/2]
        x = (top[0]+bottom[0])/2
        y = (top[1]+bottom[1])/2
        return x,y

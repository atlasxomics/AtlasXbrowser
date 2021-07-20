import tkinter as tk
from tkinter import ttk
import re
from tkinter.constants import DISABLED
from PIL import Image, ImageTk
import os
import csv
from mouse_mover import MouseMover
from tkinter import filedialog
import os
import math
import json
from tissue_grid import Tissue
import cv2


class Gui():
    def __init__(self, root):
        self.root = root
        self.root.title("Atlas Browser")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width/2) - (1200/2)
        y = (screen_height/2) - (700/2)
        self.root.geometry('%dx%d+%d+%d' % (1200, 600, x, y))


        background_image = Image.open("atlasbg.png")
        resized_image = background_image.resize((1200, 600), Image.ANTIALIAS)
        bg = ImageTk.PhotoImage(resized_image)
        background_label = tk.Label(self.root, image=bg)
        background_label.image = bg
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open Image Folder", command=self.second_window)
        #filemenu.add_command(label="Open Spatial Folder", command=self.third_window)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)


        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command="")

        self.names = []
        self.folder_selected = None



    def second_window(self):
        self.folder_selected = filedialog.askdirectory()
        for file in os.listdir(self.folder_selected):
            if file.startswith(".") == False:
                self.names.append(file)


        self.arr = None
        self.topx, self.topy, self.botx, self.boty = 0, 0, 0, 0
        self.points = []
        

        self.newWindow = tk.Toplevel(self.root)
        screen_width = self.newWindow.winfo_screenwidth()
        screen_height = self.newWindow.winfo_screenheight()
        self.newWindow.title("Atlas Browseer")
        
        self.newWindow.geometry("{0}x{1}".format(screen_width, screen_height))


        for i in self.names:
            if "BSA" in i:
                beforeA = Image.open(self.folder_selected + "/" + i)
                a = beforeA.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                self.postB_Name = self.folder_selected + "/" + i
                beforeB = Image.open(self.postB_Name)
                b = beforeB.transpose(Image.FLIP_LEFT_RIGHT)

        

        w, h = (a.width, a.height)
        self.width, self.height = (a.width, a.height)
        if w > 950 and h > 850:
            self.factorW = 950/w
            self.factorH = 850/h
            floor = a.resize((950, 850), Image.ANTIALIAS)
            postB = b.resize((950, 850), Image.ANTIALIAS)
        elif w > 950:
            self.factorW = 950/w
            self.factorH = 1
            floor = a.resize((950, h), Image.ANTIALIAS)
            postB = b.resize((950, h), Image.ANTIALIAS)
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
        
        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        flippedimage = cv2.flip(img, 1)
        try:
            self.scale_image = cv2.cvtColor(flippedimage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedimage      
        

        #containers
        self.my_canvas = tk.Canvas(self.newWindow, width = floor.width, height= floor.height, highlightthickness = 0, bd=0)
        self.my_canvas.pack(side=tk.LEFT, anchor=tk.NW) 
        self.my_canvas.old_coords = None
        frame = tk.Frame(self.newWindow, width = floor.width-w, height= h)
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.BOTH)


        #images
        self.imgA = ImageTk.PhotoImage(floor)
        self.imgB = ImageTk.PhotoImage(postB)
        self.picNames = [self.imgA, self.imgB]

        self.lmain = tk.Label(self.my_canvas)
        self.lmain.pack()
        self.lmain.img = self.imgA
        self.lmain.configure(image=self.imgA)

        #create Scales
        self.thresh_label = tk.Label(frame, text="Threshold Value Scale", font =("Courier", 14))
        self.thresh_label.place(x=17,y=10)
        self.thresh_label_value = tk.Label(frame, text="255")
        self.thresh_label_value.place(x=17,y=60)
        self.spot_label = tk.Label(frame, text="SpotRemover Value Scale", font =("Courier", 14))
        self.spot_label.place(x=17,y=80)
        self.spot_label_value = tk.Label(frame, text="17")
        self.spot_label_value.place(x=17,y=130)

        self.thresh_value = tk.IntVar()
        self.spot_value = tk.IntVar()
        self.thresh_value.set(255)
        self.spot_value.set(17)
        self.thresh_scale = ttk.Scale(frame, variable = self.thresh_value, from_ = 19, to = 255, orient = tk.HORIZONTAL, command= self.showThresh)  
        self.thresh_scale.place(x=17,y=40, relwidth=.8)
        self.spot_scale = ttk.Scale(frame, variable = self.spot_value, from_ = 0, to = 17, orient = tk.HORIZONTAL, command= self.showThresh)  
        self.spot_scale.place(x=17,y=110, relwidth=.8)


        #buttons

        self.begin_button = tk.Button(frame, text = "Place Markers", command = self.find_points, state=tk.ACTIVE)
        self.begin_button.place(relx=.3, y= 200)

        self.confirm_button = tk.Button(frame, text = "Confirm", command = lambda: self.confirm(None), state=tk.DISABLED)
        self.confirm_button.place(relx=.3, y= 230)

        self.roi_button = tk.Button(frame, text = "Show Roi", command = self.roi, state=tk.DISABLED)
        self.roi_button.place(relx=.1, y= 260)

        self.grid_button = tk.Button(frame, text = "Show Grid", command = lambda: self.grid(self.picNames[2]), state=tk.DISABLED)
        self.grid_button.place(relx=.3, y= 260)

        self.gridA_button = tk.Button(frame, text = "Show Grid on PostB", command = lambda: self.grid(self.picNames[0]), state=tk.DISABLED)
        self.gridA_button.place(relx=.5, y= 260)

        self.onoff_button = tk.Button(frame, text = "On/Off Tissue", command = self.sendinfo, state=tk.DISABLED)
        self.onoff_button.place(relx=.1, y= 290)

        self.labelframe = tk.LabelFrame(frame, text="Selection Tools")
        self.labelframe.place(relx=.5, y= 290)
        self.value_labelFrame = tk.IntVar()
        self.value_labelFrame.set(1)
        tk.Radiobutton(self.labelframe, text="One by One", variable=self.value_labelFrame, value=1, command = self.offon).pack()
        tk.Radiobutton(self.labelframe, text="Highlight", variable=self.value_labelFrame, value=2, command = self.highlit).pack()
        for child in self.labelframe.winfo_children():
            if child.winfo_class() == 'Radiobutton':
                child['state'] = 'disabled'

        self.position_file = tk.Button(frame, text = "Create Spatial Folder", command = self.create_files, state=tk.DISABLED)
        self.position_file.place(relx=.1, y= 350)

        self.Rpoints = []
        self.it = 0
        self.coords = [[[] for i in range(50)] for i in range(50)]
        

        path = os.path.join(self.folder_selected, "spatial")
        os.mkdir(path)
        
    '''
    def third_window(self):
        self.folder_selected = filedialog.askdirectory()
        for file in os.listdir(self.folder_selected):
            if file.startswith(".") == False:
                self.names.append(file)

        self.arr = None
        self.topx, self.topy, self.botx, self.boty = 0, 0, 0, 0
        self.points = []
        

        self.thirdWindow = tk.Toplevel(self.root)
        screen_width = self.thirdWindow.winfo_screenwidth()
        screen_height = self.thirdWindow.winfo_screenheight()
        self.thirdWindow.title("Atlas Browser")
        
        self.thirdWindow.geometry("{0}x{1}".format(screen_width, screen_height))


        temp = re.compile("([a-zA-Z]+)([0-9]+).image")
        res = temp.search(self.folder_selected).groups() 
        self.excelName = res[0]+ res[1]
        
        for i in self.names:
            if "json" in i:
                self.json = self.folder_selected + "/" + i

            elif "list" in i:
                self.position = self.folder_selected + "/" + i
            else:
                self.postB_Name = self.excelName + ".image/" + self.excelName + "_postB.png"
                beforeB = Image.open(self.postB_Name)
                a = beforeB.transpose(Image.FLIP_LEFT_RIGHT)

        

        w, h = (a.width, a.height)
        self.width, self.height = (a.width, a.height)
        if w > 950 and h > 850:
            self.factorW = 950/w
            self.factorH = 850/h
            floor = a.resize((950, 850), Image.ANTIALIAS)
        elif w > 950:
            self.factorW = 950/w
            self.factorH = 1
            floor = a.resize((950, h), Image.ANTIALIAS)
        elif h > 850:
            floor = a.resize((w, 850), Image.ANTIALIAS)
            self.factorH = 850/h
            self.factorW = 1
        else:
            floor = a
            self.factorW = 1
            self.factorH = 1

        self.refactor = a

        self.newWidth = floor.width ; self.newHeight = floor.height
        
        img = cv2.imread(self.postB_Name, cv2.IMREAD_UNCHANGED)
        flippedimage = cv2.flip(img, 1)
        try:
            self.scale_image = cv2.cvtColor(flippedimage, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            self.scale_image = flippedimage      
        

        #containers
        self.my_canvas = tk.Canvas(self.thirdWindow, width = floor.width, height= floor.height, highlightthickness = 0, bd=0)
        self.my_canvas.pack(side=tk.LEFT, anchor=tk.NW) 
        self.my_canvas.old_coords = None
        frame = tk.Frame(self.thirdWindow, width = floor.width-w, height= h)
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.BOTH)


        #images
        self.imgA = ImageTk.PhotoImage(floor)
        self.picNames = []

        self.lmain = tk.Label(self.my_canvas)
        self.lmain.pack()
        self.lmain.img = self.imgA
        self.lmain.configure(image=self.imgA)

        #create Scales
        self.thresh_label = tk.Label(frame, text="Threshold Value Scale", font =("Courier", 14))
        self.thresh_label.place(x=17,y=10)
        self.thresh_label_value = tk.Label(frame, text="255")
        self.thresh_label_value.place(x=17,y=60)
        self.spot_label = tk.Label(frame, text="SpotRemover Value Scale", font =("Courier", 14))
        self.spot_label.place(x=17,y=80)
        self.spot_label_value = tk.Label(frame, text="17")
        self.spot_label_value.place(x=17,y=130)

        self.thresh_value = tk.IntVar()
        self.spot_value = tk.IntVar()
        self.thresh_value.set(255)
        self.spot_value.set(17)
        self.thresh_scale = ttk.Scale(frame, variable = self.thresh_value, from_ = 19, to = 255, orient = tk.HORIZONTAL, command= self.showThresh)  
        self.thresh_scale.place(x=17,y=40, relwidth=.8)
        self.spot_scale = ttk.Scale(frame, variable = self.spot_value, from_ = 0, to = 17, orient = tk.HORIZONTAL, command= self.showThresh)  
        self.spot_scale.place(x=17,y=110, relwidth=.8)


        #buttons

        self.grid_button = tk.Button(frame, text = "Load Grid", command = lambda: [self.confirm(None), self.grid(self.picNames[0]) ])
        self.grid_button.place(relx=.3, y= 260)

        self.onoff_button = tk.Button(frame, text = "On/Off Tissue", command = self.sendinfo, state=tk.DISABLED)
        self.onoff_button.place(relx=.3, y= 290)

        self.position_file = tk.Button(frame, text = "Create Spatial Folder", command = self.loadinfo, state=tk.DISABLED)
        self.position_file.place(relx=.3, y= 320)

        f = open(self.json)
        data = json.load(f)
        self.Rpoints = data['original_points']
        self.it = 0
        self.coords = [[[] for i in range(50)] for i in range(50)]
    '''





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
            
            

    def json_file(self):
        factorHigh = 0
        factorLow = 0
        path = os.path.join(self.folder_selected, "spatial")
        

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
        self.thresh_scale['state'] = tk.DISABLED
        self.spot_scale['state'] = tk.DISABLED

        self.lmain.destroy()
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgA, state="disabled")
        
        mm = MouseMover(self.my_canvas)
        self.my_canvas.bind("<Button-1>", mm.find_object)
        self.my_canvas.bind("<B1-Motion>", mm.drag)
        
        self.my_canvas.create_polygon(10,10,  20,10,  20,20, 10,20,  10,10,fill="", outline="blue", width=1, tags="point"+str(self.it)+"1")
        self.my_canvas.create_polygon(self.my_canvas.winfo_width()-20,10, self.my_canvas.winfo_width()-10,10,self.my_canvas.winfo_width()-10,20,self.my_canvas.winfo_width()-20,20,self.my_canvas.winfo_width()-20,10, fill="", outline="blue", width=1, tags="point"+str(self.it)+"2")
        self.my_canvas.create_polygon(10,self.my_canvas.winfo_height()-20, 20,self.my_canvas.winfo_height()-20,  20,self.my_canvas.winfo_height()-10, 10,self.my_canvas.winfo_height()-10, 10,self.my_canvas.winfo_height()-20, fill="", outline="blue", width=1, tags="point"+str(self.it)+"3")
        self.my_canvas.create_polygon(self.my_canvas.winfo_width()-20,self.my_canvas.winfo_height()-20,  self.my_canvas.winfo_width()-10,self.my_canvas.winfo_height()- 20,   self.my_canvas.winfo_width()-10,self.my_canvas.winfo_height()- 10,  self.my_canvas.winfo_width()-20,self.my_canvas.winfo_height()-10,  self.my_canvas.winfo_width()-20,self.my_canvas.winfo_height()-10, fill="", outline="blue", width=1, tags="point"+str(self.it)+"4")

        self.confirm_button["state"] = tk.ACTIVE
        
    
    def highlight(self, event):
        self.topx, self.topy = event.x, event.y
        self.my_canvas.create_rectangle(self.topx, self.topy, self.topx, self.topy,dash=(2,2), fill='', tag= "highlight", outline='black')

    def release(self,event):
        for k in self.my_canvas.find_overlapping(self.topx, self.topy, self.botx, self.boty):
            position = event.widget.gettags(k)
            if len(position) > 0 and position[0]!="highlight":
                where = position[0].split("x")
                state = self.my_canvas.itemcget(k,'state')
                i = where[0]
                j = where[1]
                if state == "normal":
                    self.my_canvas.itemconfig(k, fill="", state="disabled")
                    
                else:
                    self.my_canvas.itemconfig(k, fill="red", stipple="gray50", state ="normal")
                    self.arr[int(i)][int(j)] = 1
        self.my_canvas.coords("highlight", 0,0,0,0)

    def update_sel_rect(self, event):
        self.my_canvas.bind("<ButtonRelease-1>", self.release)
        self.botx, self.boty = event.x, event.y
        self.my_canvas.coords("highlight", self.topx, self.topy, self.botx, self.boty)  # Update selection rect.
        

    
    def on_off(self, event):
        tag = event.widget.find_closest(event.x,event.y)
        position = event.widget.gettags(tag)
        where = position[0].split("x")
        state = self.my_canvas.itemcget(tag,'state')
        i = where[0]
        j = where[1]
        if state ==  "normal":
            self.my_canvas.itemconfig(tag, fill="", stipple="", state="disabled")
            self.arr[int(i)][int(j)] = 0
        else:
            self.my_canvas.itemconfig(tag, fill="red", stipple="gray50", state ="normal")
            self.arr[int(i)][int(j)] = 1
        
    def create_files(self):
        my_file = open("barcode.txt","r")
        excelC = 1
        path = os.path.join(self.folder_selected, "spatial")
        with open(path + "/tissue_positions_list.csv", 'w') as f:
            writer = csv.writer(f)

            for i in range(50):
                for j in range(50):
                    barcode = my_file.readline().split('\t')
                    if self.arr[j][i] == 1:
                        writer.writerow([barcode[0].strip(), 1, i, j, self.coords[j][i][1], self.coords[j][i][0]])
                    else:
                        writer.writerow([barcode[0].strip(), 0, i, j, self.coords[j][i][1], self.coords[j][i][0]])

                excelC += 1
              
        my_file.close()
        self.json_file()
        f.close()
                
                
    def confirm(self, none):
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
        

        if len(self.picNames) > 0:
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
            self.picNames.append(bw_Image)
            self.confirm_button["state"] = tk.DISABLED
            self.begin_button["state"] = tk.DISABLED
            self.roi_button["state"] = tk.ACTIVE
            self.grid_button["state"] = tk.ACTIVE
            self.gridA_button["state"] = tk.ACTIVE
            self.onoff_button["state"] = tk.ACTIVE
            
        else:
            self.onoff_button["state"] = tk.ACTIVE
            self.picNames.append(bw_Image)
            self.lmain.destroy()
        
        

    
    def roi(self):
        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = self.imgB)
        self.my_canvas.create_polygon(self.Rpoints, fill ="",outline="black", tags="roi")

    def grid(self,pic):

        self.my_canvas.delete("all")
        self.my_canvas.create_image(0,0, anchor="nw", image = pic, state="disabled")

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
        matta = Tissue(points_copy, self.factorW, self.factorH, dbit)
        self.arr,self.spot_dia, self.fud_dia = matta.thaanswer()
        for i in range(len(self.arr)):
            for j in range(len(self.arr)):
                position = str(j) + "x" + str(i)
                if self.arr[j][i] == 1:
                    try:
                        self.my_canvas.itemconfig(position, fill='red', stipple="gray50", state = "normal")
                        self.my_canvas.itemconfig(10+i*50+j, fill='red', state="normal")
                    except tk.TclError:
                        pass

    def loadinfo(self):
        my_file = open("barcode.txt","r")
        excelC = 1
        with open(self.folder_selected + "/tissue_positions_list.csv", 'w') as f:
            writer = csv.writer(f)

            for i in range(50):
                for j in range(50):
                    barcode = my_file.readline().split('\t')
                    if self.arr[j][i] == 1:
                        writer.writerow([barcode[0].strip(), 1, i, j, self.coords[j][i][1], self.coords[j][i][0]])
                    else:
                        writer.writerow([barcode[0].strip(), 0, i, j, self.coords[j][i][1], self.coords[j][i][0]])

                excelC += 1
              
        my_file.close()
        f.close()


    def center(self,tL,tR,bR,bL):
        top = [(tL[0]+tR[0])/2,(tL[1]+tR[1])/2]
        bottom = [(bL[0]+bR[0])/2,(bL[1]+bR[1])/2]
        x = (top[0]+bottom[0])/2
        y = (top[1]+bottom[1])/2
        return x,y

    def offon(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.unbind('<B1-Motion>')
        self.my_canvas.unbind('<ButtonRelease-1>')
        self.my_canvas.bind('<Button-1>',self.on_off)
    def highlit(self):
        self.my_canvas.unbind('<Button-1>')
        self.my_canvas.bind('<Button-1>',self.highlight)
        self.my_canvas.bind('<B1-Motion>', self.update_sel_rect)
        

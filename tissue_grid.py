from tkinter import *
from PIL import Image
import cv2
import math


class Tissue():
    def __init__(self, points, wfactor, hfactor, dbit, excelName):
        thresh = cv2.imread(dbit, cv2.IMREAD_UNCHANGED)


        for i in range(len(points)):
            if i % 2 == 0:
                points[i] /= wfactor
            else:
                points[i] /= hfactor

        #getting the slope of left * right lines
        leftS = self.ratio50l(points[0],points[1],points[6],points[7],1)
        topS = self.ratio50l(points[0],points[1],points[2],points[3],1)
        slope = [round(leftS[1]-points[1], 5), round(leftS[0]-points[0], 5)]
        slopeT = [round(topS[1]-points[1], 5), round(topS[0]-points[0], 5)]
        slopeO = [slope[0]*2, slope[1]*2]
        slopeTO = [slopeT[0]*2, slopeT[1]*2]


        dist= round(self.distance(points[0], points[1], points[2], points[3]), 5)
        distance = int(dist/99)
        p = round(self.distance(points[0], points[1], topS[0]+slope[1], topS[1]+slope[0]), 5)
        q = round(self.distance(leftS[0], leftS[1], topS[0], topS[1]), 5)
        self.area = (p*q) / 2

        numChannels = 50
        self.arr = [[0 for i in range(50)] for i in range(50)]
        top = [0,0]
        left = [0,0]
        flag = False
        prev = [points[0],points[1]]
        corners = []
        for i in range(0, numChannels):
            top[0] = prev[0]+slopeT[1]
            top[1] = prev[1]+slopeT[0]
            flag = False
            for j in range(0, numChannels):
                corners = []
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

                corners.append(tL);corners.append(tR);corners.append(bR);corners.append(bL);
                
                if self.calculate_avg(thresh, corners, self.area, distance) > 250:
                    self.arr[j][i] = 0
                else:
                    self.arr[j][i] = 1

                top[0] += slopeO[1]
                top[1] += slopeO[0]
            prev[0] += slopeTO[1]
            prev[1] += slopeTO[0]

        self.thaanswer()

    def calculate_avg(self,pic, points, divider, dist):
        sum = 0
        w = pic.shape[1] - 1
        h = pic.shape[0] - 1
        topCoords = self.coords(points[0], points[1], dist)
        for i in topCoords:
            downCoords = self.downCoords(i, dist)
            for j in downCoords:
                sum += pic[min(h,round(j[1])), min(w,round(j[0]))]
        return sum/divider

    def ratio50l(self,xc,yc,xr,yr,a):
        txp = xc + (a/(99))*(xr-xc)
        typ = yc + (a/(99))*(yr-yc)
        return [txp , typ]

    def coords(self, tL,tR,dis):
        coords = []
        coords.append(tL)
        for i in range(1,dis+1):
            txp = tL[0] + (i/(dis))*(tR[0]-tL[0])
            typ = tL[1] + (i/(dis))*(tR[1]-tL[1])
            coords.append([txp,typ])
        return coords
    def downCoords(self, points, dis):
        coords = []
        coords.append(points)
        for i in range(1, dis+1):
            y = points[1]+ i
            x = points[0]
            coords.append([x,y])
        return coords

    def distance(self,x1,y1,x2,y2):
        dis = (x1-x2)**2 + (y1-y2)**2
        return math.sqrt(dis)

    def thaanswer(self):
        return self.arr,self.area
    
    
    



        
    


        
            

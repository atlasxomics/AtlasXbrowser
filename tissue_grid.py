from tkinter import *
from PIL import Image
import cv2
import math
from chip_geometry import ChipGeometry


class Tissue():
    def __init__(self, points, factor, dbit, num_chan, geometry=None):
        thresh = cv2.imread(dbit, cv2.IMREAD_UNCHANGED)


        for i in range(len(points)):
            points[i] /= factor

        geometry = geometry or ChipGeometry.preset(25)
        slope, slopeT, slopeO, slopeTO = geometry.slopes(points, num_chan)
        self.spot_dia, self.fud_dia = geometry.diameters(points, num_chan)

        numChannels = num_chan
        self.tixel_status = [[0 for i in range(numChannels)] for i in range(numChannels)]
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
                if self.calculate_avg(thresh, corners) > 242:
                    self.tixel_status[j][i] = 0
                else:
                    self.tixel_status[j][i] = 1

                top[0] += slopeO[1]
                top[1] += slopeO[0]
            prev[0] += slopeTO[1]
            prev[1] += slopeTO[0]

        self.theAnswer()

    def calculate_avg(self, pic, points, dist=None):
        """Sample inside the capture parallelogram, excluding inter-tixel gaps."""
        origin, right, _, bottom = points
        horizontal = [right[i] - origin[i] for i in range(2)]
        vertical = [bottom[i] - origin[i] for i in range(2)]
        nx = max(1, math.ceil(math.hypot(*horizontal)))
        ny = max(1, math.ceil(math.hypot(*vertical)))
        total = 0.0
        count = 0
        height, width = pic.shape[:2]
        for col in range(nx):
            for row in range(ny):
                x, y = [math.floor(origin[i] + (col + .5)/nx * horizontal[i]
                                   + (row + .5)/ny * vertical[i]) for i in range(2)]
                if 0 <= x < width and 0 <= y < height:
                    total += float(pic[y, x])
                    count += 1
        return total/count if count else 255

    def ratio50l(self,xc,yc,xr,yr,num):
        txp = xc + (1/(num))*(xr-xc)
        typ = yc + (1/(num))*(yr-yc)
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

    def theAnswer(self):
        return self.tixel_status,self.spot_dia,self.fud_dia
    
from __future__ import print_function
import cv2 as cv
import argparse
 
max_value = 252
max_type = 4
max_binary_value = 252
trackbar_type = 'Type: \n 0: Binary \n 1: Binary Inverted \n 2: Truncate \n 3: To Zero \n 4: To Zero Inverted'
trackbar_value = 'Value'
window_name = 'Threshold Demo'
 
## [Threshold_Demo]
def Threshold_Demo(val):
    threshold_value = cv.getTrackbarPos(trackbar_value, window_name)
    #_, dst = cv.threshold(src_gray, threshold_value, max_binary_value, threshold_type )
    dst = cv.adaptiveThreshold(src_gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, threshold_value+3, 13)
    print(threshold_value+3)
    cv.imshow(window_name, dst)
    #cv.imwrite("bw.png", dst)
## [Threshold_Demo]
 
parser = argparse.ArgumentParser(description='Code for Basic Thresholding Operations tutorial.')
#Update the Location of your image here
parser.add_argument('--input', help='D97.image/D97_postB.png', default='D97.image/D97_postB.png')
args = parser.parse_args()
 
## [load]
# Load an image
src = cv.imread(cv.samples.findFile(args.input))
if src is None:
    print('Could not open or find the image: ', args.input)
    exit(0)
# Convert the image to Gray
src_gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
blurred = cv.GaussianBlur(src_gray, (19,19), 5)
## [load]
 
## [window]
# Create a window to display results
cv.namedWindow(window_name)
## [window]
 
## [trackbar]
# Create Trackbar to choose type of Threshold
# Create Trackbar to choose Threshold value
cv.createTrackbar(trackbar_value, window_name , 0, max_value, Threshold_Demo)
## [trackbar]
 
# Call the function to initialize
Threshold_Demo(0)
# Wait until user finishes program
cv.waitKey()
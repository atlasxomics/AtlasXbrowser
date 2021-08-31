"""Register an image to a reference image, python regimg.py -h
"""
import cv2
import numpy as np
import argparse

ap = argparse.ArgumentParser(
    description="Registering an image against a reference image",
    epilog="Image needs to be cropped to be similar size")

ap.add_argument("-i", "--input", required=True, help="Path to the inputfile")
ap.add_argument("-r", "--ref", required=True, help="Path to the reference image")
ap.add_argument("-o", "--output", required=True, help="Path to the outputfile")
 
args = vars(ap.parse_args())

input_file = args["input"]
output_file = args["output"]
ref_file = args["ref"]

# Open the image files.
img1_color = cv2.imread(input_file)  # Image to be aligned.
img2_color = cv2.imread(ref_file)    # Reference image.
  
# Convert to grayscale.
img1 = cv2.cvtColor(img1_color, cv2.COLOR_BGR2GRAY)
img2 = cv2.cvtColor(img2_color, cv2.COLOR_BGR2GRAY)
height, width = img2.shape
  
# Create ORB detector with 8000 features.
orb_detector = cv2.ORB_create(5000)
  
# Find keypoints and descriptors.
# The first arg is the image, second arg is the mask
#  (which is not reqiured in this case).
kp1, d1 = orb_detector.detectAndCompute(img1, None)
kp2, d2 = orb_detector.detectAndCompute(img2, None)
  
# Match features between the two images.
# We create a Brute Force matcher with 
# Hamming distance as measurement mode.
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck = True)
  
# Match the two sets of descriptors.
matches = matcher.match(d1, d2)
  
# Sort matches on the basis of their Hamming distance.
matches.sort(key = lambda x: x.distance)
  
# Take the top 90 % matches forward.
matches = matches[:int(len(matches)*5)]
no_of_matches = len(matches)
  
# Define empty matrices of shape no_of_matches * 2.
p1 = np.zeros((no_of_matches, 2))
p2 = np.zeros((no_of_matches, 2))
  
for i in range(len(matches)):
  p1[i, :] = kp1[matches[i].queryIdx].pt
  p2[i, :] = kp2[matches[i].trainIdx].pt
  
# Find the homography matrix.
homography, mask = cv2.findHomography(p1, p2, cv2.RANSAC)
  
# Use this matrix to transform the
# colored image wrt the reference image.
transformed_img = cv2.warpPerspective(img1_color,
                    homography, (width, height))
  
# Save the output.
cv2.imwrite(output_file, transformed_img)

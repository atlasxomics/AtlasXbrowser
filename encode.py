import base64
import argparse

ap = argparse.ArgumentParser(
    description="Encode an image",
    epilog="Image will be encoded for creating executable")

ap.add_argument("-i", "--input", required=True, help="Path to the inputfile")

args = vars(ap.parse_args())

input_file = args["input"] 
with open(input_file, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read())
print(encoded_string)

# AtlasXBrowser
#################################################################################

Interactive browser for AtlasXomics Data

This software is designed as an interactive browser for processing AtlasXomics image Data

## Download

    git clone https://github.com/atlasxomics/AtlasXBrowser.git
    cd AtlasXBrowser
    git clone https://github.com/formazione/Azure-ttk-theme

## Dependencies

Need python 3.7. Follow steps below to install required libraries (Mac OS X):
  
    sudo easy_install pip (admin)
    pip install scipy
    pip install seaborn
    pip install tifffile
    pip install jsbeautifier
    pip install pandas
    pip install pillow
    pip install matplotlib
    pip install opencv-python

Get pip installed if not admin

    curl https://bootstrap.pypa.io/get-pip.py -o ~/Downloads/get-pip.py
    python3 ~/Downloads/get-pip.py --user
    export PATH="/Users/YOUR_USAER_NAME/.local/bin:$PATH"

To get python installed:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    export PATH="/usr/local/opt/python/libexec/bin:$PATH"
    brew install python@3.7
    
## Usage

Update to the latest version before running

    cd AtlasXBrowser
    git pull https://github.com/atlasxomics/AtlasXBrowser.git
    
Run the program with following command:

    python ABrowser.py

## Input data

The input image folder contains either

    Dxx_postB.tif
    Dxx_postB_BSA.tif

or a 'spatial' folder contains following files for updating the position file

    tissue_hires_image.png
    tissue_lowres_image.png
    scalefactors_json.json
    tissue_positions_list.csv
    metadata.json
    
 ## Operation tips
 
1. Image filenames have to be Dxx_postB and Dxx_postB_BSA with extentisions
2. If the ROI is too small in the image, you may want to crop both images then register them in the terminal
   
   ```
   python regimg.py -r Dxx_postB.tif -i Dxx_postB_BSA.tif -o registered_BSA.tif
   mv registered_BSA.tif Dxx_postB_BSA.tif
   ```
   
3. Images are automatically flipped from left to right by the software, no need to flip them manually
4. You will need to rotate both images 90 degree counter-clockwise if it is from keyence

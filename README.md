# AtlasBrowser
#################################################################################

Interactive browser for AtlasXomics Data

This is designed as an interactive browser for processing AtlasXomics image Data

## Download

    git clone https://github.com/atlasxomics/AtlasBrowser.git

## Dependencies

Need python 3.6 or higher. Follow steps below to install required libraries (Mac OS X):
  
    sudo easy_install pip (admin)
    pip install pillow
    pip install opencv-python
    pip install matplotlib
    pip install pandas

Get pip installed if not admin

    curl https://bootstrap.pypa.io/get-pip.py -o ~/Downloads/get-pip.py
    python ~/Downloads/get-pip.py --user
    export PATH="/Users/YOUR_USAER_NAME/.local/bin:$PATH"

To get python installed:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    export PATH="/usr/local/opt/python/libexec/bin:$PATH"
    brew install python@3.7
    
## Usage
Run the program with following command:

    python run_the_app.py

## The input image folder contains either

    Dxx_postB.TIFF
    Dxx_postB_BSA.TIFF

or a 'spatial' folder contains following files for updating the position file

    tissue_hires_image.png
    tissue_lowres_image.png
    scalefactors_json.json
    tissue_positions_list.csv
    metadata.json
    
 ## Operation tips
 
     

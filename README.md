# AtlasXBrowser
#################################################################################

Interactive browser for AtlasXomics Data

This software is designed as an interactive browser for processing AtlasXomics image Data. To learn more about AtlasXbrowser please visit the documentation, https://docs.atlasxomics.com/projects/AtlasXbrowser/en/latest/.

## Download

    git clone https://github.com/atlasxomics/AtlasXBrowser.git
    cd AtlasXBrowser

## Dependencies
Due to the numerous dependencies as well as the requirement of running Python 3.7, we reccomend the usage of Anaconda.
If Anaconda is not currently installed on your system see the following https://docs.anaconda.com/anaconda/install/index.html.

To ensure conda is installed run:

    conda --version

Upon running the command with no errors, ensure conda is running the latest distribution by running:
    
    conda update conda

To create an enviroment running Python 3.7, run:

    conda create --name py37 python=3.7
    
Where "py37" is any desired name of the enviroment.

To activate the enviroment:
    
    conda deactivate
    conda activate py37
    
To ensure the proper version of python is being run enter:

    python --version

This should return Python 3.7.xx. If If this is not the case, deactivate the conda enviroment using "conda deactivate'. Repeat this command until there is no conda enviorment listed at the left side of the terminal and then reactivate the enviroment.

Once the conda enviroment is setup and running, run the following commands to install the required packages.

      conda install -c conda-forge scipy
      conda install -c conda-forge seaborn
      conda install -c conda-forge tifffile
      conda install -c conda-forge jsbeautifier
      conda install -c conda-forge pandas
      conda install -c conda-forge pillow
      conda install -c conda-forge matplotlib
      conda install -c fastai opencv-python-headless
    
## Usage

Update to the latest version before running

    cd AtlasXBrowser
    git pull https://github.com/atlasxomics/AtlasXBrowser.git
    
Run the program with following command:

    python ABrowser.py

See the documentation for more details about using AtlasXbrowser, https://docs.atlasxomics.com/projects/AtlasXbrowser/en/latest/.

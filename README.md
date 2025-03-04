# AtlasXBrowser
#################################################################################

Interactive browser for AtlasXomics Data

This software is designed as an interactive browser for processing AtlasXomics image Data. To learn more about AtlasXbrowser please visit the documentation, [https://docs.atlasxomics.com/projects/AtlasXbrowser/en/latest/](https://atlasxbrowser-docs.readthedocs.io/en/latest/).

## Download

    git clone https://github.com/atlasxomics/AtlasXBrowser.git
    cd AtlasXBrowser

## Dependencies
Use pyenv or conda to create a python enviornment with verzion 3.8.8

To create an environment with pyenv:

    pyenv install 3.8.8
    pyenv virtualenv 3.8.8 abrowser

To activate the enviroment:
    
    pyenv activate myenv
    pyenv deactivate

    
To create an enviroment with conda:

    conda create --name abrowser python=3.8.8

To activate the enviroment:
    
    conda deactivate
    conda activate abrowser
    
To ensure the proper version of python is being run enter:

    python --version

This should return Python 3.8.8. If If this is not the case, deactivate the enviroment. Repeat this command until there is no enviorment listed at the left side of the terminal and then reactivate the enviroment.

Once the enviroment is setup and running, run the following commands to install the required packages.

      pip install -r requirements.txt
    
## Usage

Update to the latest version before running

    cd AtlasXBrowser
    git pull https://github.com/atlasxomics/AtlasXBrowser.git
    
Run the program with following command:

    python ABrowser.py

See the documentation for more details about using AtlasXbrowser, [https://docs.atlasxomics.com/projects/AtlasXbrowser/en/latest/](https://atlasxbrowser-docs.readthedocs.io/en/latest/).

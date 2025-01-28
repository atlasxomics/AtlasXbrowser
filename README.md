# AtlasXBrowser
#################################################################################

This branch is used to create an executable 
All necessary python packages are in requirements.txt

The Dockerfile is for a linux container

Command to run to create the executable on hostmachine. Will only be useable by machine with the same OS
pyinstaller --onefile ABrowser.py

Path to executable is /dist/Abrowser

Run the below commands to generate linux_exe
docker build -t abrowser-linux . 
docker run -it abrowser-linux  
docker cp <container-id>:/srv/abrowser/dist/ABrowser ./linux_exe

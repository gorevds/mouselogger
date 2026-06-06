# MouseLogger #

##### 1. How to install?
Run install.bat. And then don't delete or move the folder with the MouseLogger.exe file.

##### 2. Where are logs?
All logs are collected in the directory C:\\MouseLog\

##### 3. How to uninstall?
Run uninstall.bat. Then an archive with all logs will be generated in the C:\\MouseLog\ folder.

##### 4. What is venv?
This is a virtual environment in case you don't have python 3.


### Information for builds ###
pyinstaller --onefile --windowed --name MouseLogger --hidden-import=win32timezone main.py

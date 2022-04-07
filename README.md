# simview
python GUI for simpson



Shortcuts
------------
Ctrl + R  Run

Ctrl + K  Kill

Ctrl + L  Clear Log



Ctrl + P  Purge selected line

Ctrl + Shift + P Purge all lines  



Ctrl + Q  Toggle crosshair

Ctrl + E  Export graphic

rest is explained in the menu bar; Edit in simview.py file by searching for ```setShortcut('Ctrl+1')``` where 1 represents the letter you want to change. Change it, save it, run it. Should be easy. Description is automatically changed.



Requirements
------------

simview requires:
- [python 3](http://python.org/download/)

And the following python packages:
- [numpy](http://sourceforge.net/projects/numpy/files/NumPy/)
- [matplotlib](http://matplotlib.org/)
- [PyQt5](http://www.riverbankcomputing.com/software/pyqt/download)

On Ubuntu and Debian these packages can be installed using the package manager:
```
sudo apt-get install python3 python3-numpy python3-matplotlib python3-pyqt5 
```

On Windows (and macOS) these packages can easily be installed by downloading [Anaconda](https://www.anaconda.com/distribution/).
It is a bit bulky but you get all popular python tools. During installation, you may enable the 
'Add Anaconda to the system PATH environment variable' box but it can interfere with TCL setup needed
 for simpson. I have not done that and use "Anaconda Prompt" application installed together with Anaconda.

Installation
------------

### Linux and macOS ###

To install simview, copy the Simpson-View directory to your favourite location. Navigate to this 
directory. Start simview by executing 
```python3 simview.py```

### Windows ###

Users that have installed python via the Anaconda program descibed above can do the following:
To install simview, copy the Simpson-View directory to your favourite location.
Start "Anaconda prompt", navigate to the Simpson-view directory and execute ```python simview.py```

Configure SIMPSON executable
------------------------------

Edit file simview.py to set properly these values (top of the file)
```
SIMPSON_EXECUTABLE="C:\\Myprograms\\simpson\\simpson.exe"
SIMPSON_TCL_LIBRARY="C:\\Myprograms\\simpson\\tcl8.6"
SIMPSON_LD_LIBRARY_PATH=""
LOCALE_ENCODING="cp852"
```
These values depend on your environment. SIMPSON_TCL_LIBRARY is _path_ to the directory tcl8.6 where 
you can find the file init.tcl. SIMPSON_LD_LIBRARY_PATH is _path_ to libraries that simpson uses 
(.dll on windows - usually sitting together with simpson.exe and we not need to set this; .so on linux)
To find out your LOCALE_ENCODING on linux, execute ```locale``` and read the encoding as the suffix to variables displayed (UTF-8).
On windows, open cmd.exe and execute ```chcp``` (cp852 is code page used on my czech laptop)
 

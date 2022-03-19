# simview
python GUI for simpson

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
During installation, you may enable the 'Add Anaconda to the system PATH environment variable' box but it can interfere with TCL setup needed for simpson.
I have not done that and use "Anaconda Prompt" application installed together with Anaconda.

Installation
------------

### Linux and macOS ###

To install simview, copy the Simpson-View directory to your favourite location.
simview can then be run by executing 'python3 /InstallPath/simview.py'.
Aliases or symlinks can be used to create a shortcut to start the program.

### Windows ###

Users that have installed python via the Anaconda progrom descibed above can do the following:
To install simview, copy the Simpson-View directory to your favourite location.
Start "Anaconda prompt" and execute 'python C:\InstallPath\simview.py'

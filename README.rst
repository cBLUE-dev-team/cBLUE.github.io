comprehensive Bathymetric Lidar Uncertainty Estimator (cBLUE)
=============================================================

cBLUE is a tool to calculate the total propagated uncertainty of bathymetric lidar data.  Currently, the tool only supports the Riegl VQ-880-G system, but development plans include adding support for the Chiroptera II system.

Installation
============

cBLUE is designed to run on 64-bit Python 2.7.  Support for Python 3 is deferred to future versions (hopefully by 1/1/2020, when Python 2 will no longer be maintained!! https://pythonclock.org/).  

cBLUE is currently provided as a collection of Python modules (.py files) and supporting text files.  The cBLUE GUI is accessed by running the CBlueApp.py file via the command line or a Python IDE. 

Starting the GUI
----------------
The GUI can be initiated from the command line with the following command (specify the full path of Gui.py if the current directory is not the location of Gui.py):

NOTE: If there are multiple Python installations on the computer running the GUI, ensure the desired installation is specified in the path environment variables or explicitly specify the full path of the relevant python executable in the command. For example:

	(command line)> C:\\Python27\\64-bit\\python.exe Gui.py

The GUI can also be initiated by running the Gui.py file from a Python IDE, such as IDLE or PyCharm.

Documentation
=============

Access cBLUE documentation by opening docs/index.html (from your local repo) in a web browser.  
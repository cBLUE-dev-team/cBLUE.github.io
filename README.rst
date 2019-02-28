comprehensive Bathymetric Lidar Uncertainty Estimator (cBLUE)
=============================================================

cBLUE is a tool to calculate the total propagated uncertainty of bathymetric lidar data.  Currently, the tool only supports the Riegl VQ-880-G system, but development plans include adding support for the Chiroptera II system.

Installation
============

cBLUE is designed to run on 64-bit Python 2.7.  Rigorous performance testing was not conducted during tool development, but memory errors were encountered when not using a 64-bit installation of Python to process the Marcos Island test dataset.  Support for Python 3 is deferred to future versions.  

cBLUE is currently provided as a collection of Python modules (.py files) and supporting text files.  The cBLUE GUI is accessed by running the CBlueApp.py file via the command line or a Python IDE. 

cBLUE Files
-----------

The following table lists the major files comprising cBLUE:

.. csv-table:: cBLUE files
	:header: file, description, relative location
	:widths: 14, 30, 10

	CBlueApp.py, initiates the GUI
	Sbet.py, loads the ASCII trajector files (or sbets), ./
	Las.py, loads the las files, ./
	Merge.py, merges the trajectory and las data based on timestamps, ./
	Tpu.py, calculates the TPU (combined subaerial and subaqueous), ./
	Subaerial.py, calculates the subaerial TPU, ./
	Subaqueous.py, calculates the subaqueous TPU, ./
	Datum.py, loads the zone-specific VDatum zone MCU, ./
	ECKV_LUT_HG0995_1sig.csv, Model coefficient look-up table for subaqueous TPU, ./lookup_tables/
	THU.csv, Riegl coefficient look-up table for subaqueous TPU, ./lookup_tables/
	V_Datum_MCU_Values.txt, contains the MCU for each VDatum zone, ./lookup_tables/


Dependencies
------------
The recommended way to ensure that all of the necessary dependencies are loaded is to create a conda environment from the text file cBLUE_install.txt using the following command, 

	conda env create --file <evn file name>
	
where <env file name> is the path to cBLUE_install.txt, which is included in the cBLUE GitHub repository.  If you don't have access to the private cBLUE repository, please send a request to nick.forfinski@gmail.com, with your GitHub username.

The major dependencies are summarized in the table below:

=======		=============================================================================
package		comment
=======		=============================================================================
numpy		most of the matrix calculations are based on numpy arrays
numexpr		used to speed up numpy-array calculations of large arrays
sympy		used to symbolically form geolocation equation and evaluate Jacobian
pandas		certain operations are based on Pandas dataframes
pathos		multiprocess framework (if user specifies multiprocessing)
laspy		used to read LAS files
Tkinter		used to create GUI
=======		=============================================================================

Starting the GUI
----------------
The GUI can be initiated from the command line with the following command (specify the full path of Gui.py if the current directory is not the location of Gui.py):

NOTE: If there are multiple Python installations on the computer running the GUI, ensure the desired installation is specified in the path environment variables or explicitly specify the full path of the relevant python executable in the command. For example:

	(command line)> C:\\Python27\\64-bit\\python.exe Gui.py

The GUI can also be initiated by running the Gui.py file from a Python IDE, such as IDLE or PyCharm.

Documentation
=============

Access cBLUE documentation by opening docs/index.html (from your local repo) in a web browser.  
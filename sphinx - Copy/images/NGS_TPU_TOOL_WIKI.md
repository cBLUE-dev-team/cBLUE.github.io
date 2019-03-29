##### Table of Contents  
[Overview](#overview)
* [Subaerial Component](#subaerial-component)  
* [Subaqueous Component](#subaqueous-component) 

[Installation and Dependencies](#installation-and-dependencies)  
* [Python Packages](#required-python-packages)
* [LAS Tools](#required-las-tools)

[Workflow](#workflow)  
* [Open Gui](#open-gui)
* [Specify Data Directories](#data-directories)
* [Specify Parameters](#specify-parameters)  
  * [Subaqueous Parameters](#sub-aqueous-parameters)  
  * [Vertical Datum Transformation Parameters](#vertical-datum-transformation-parameters)  
* [Pre-Process Tiles](#pre-process-tiles)  
* [Load SBET Files](#load-sbet-files)  
* [Process TPU](#process-tpu)  

[Output](#output)  
* [TPU Data File](#tpu-data-file)  
* [TPU Metadata File](#tpu-metadata-file)  

## Overview
This tool, coded in Python, computes the vertical total propagated uncertainty (TPU) of bathymetry acquired with a Riegl VQ-880-G topobathymetric lidar.  The algorithm consists of subaerial and subaqueous components.  
![](http://web.engr.oregonstate.edu/~forfinsn/NGS_TPU_TOOL/GeneralApproach.png)  
_Image Credit:  Chris Parrish_

#### Subaerial Component
The subaerial component analytically computes the TPU of the laser pulse at the water surface using the equations shown below.  The calculations include polynomial surface fitting to model the differences between the proprietary scan pattern and the implemented scan pattern.  
![](http://web.engr.oregonstate.edu/~forfinsn/NGS_TPU_TOOL/SubaerialLaserGeolocationEquation.png)  
_Image Credit:  Jaehoon Jung_

#### Subaqueous Component
The subaqueous component stochastically computes the TPU of the laser pulse on the seafloor using Monte Carlo ray tracing based on surface modeling and estimates of scattering and absorption (see the figure below).  To minimize the computational complexity of performing Monte Carlo simmulations for large numbers of data points (> 1 billion), the algorithm relies of pre-computed coefficient lookup tables.  
![](http://web.engr.oregonstate.edu/~forfinsn/NGS_TPU_TOOL/SubaqueousMonteCarlo.gif)  
_Image Credit:  Firat Eren_

## Installation and Dependencies
The TPU tool consists of 10 files, which reside in the same folder.  

File | Description
--- | ---
Gui.py | the main file to run to initiate the tool GUI
DirectorySelectbutton.py | GUI helper class
RadioFrame.py | GUI helper class
pre_tPU_tile_processing.py | the code that calls the 4 LAS Tool executables to generate the time-sorted bathy-only flight line files that are the input to the TPU algorithm
load_sbet.py | the code that loads the trajectory data contained in the ASCII SBET files
calc_aerial_TPU.py | the code that performs the subaerial component of the TPU algorithm
SubAqueous.py | the code that performs the subaqueous component of the TPU algorithm

The TPU tool has the following dependencies:  

<a name="required-python-packages"></a>_Required Python Packages_  

Python Package | Comment
--- | ---
numpy | most of the matrix calculations are based on numpy arrays
numexpr | used to speed up numpy-array calculations of large arrays
sympy | used to symbolically calculated large Jacobian equations involving numerous trig functions
pandas | files are imported and exported using pandas dataframes
laspy | used to read LAS files directly
subprocess | used to call LAS tools executables from within the GUI
Tkinter | used to create GUI
DirectorySelectButton | GUI component
RadioFrame | GUI component
time | -
datetime | -
math | -
os | -  
  
<a name="required-las-tools"></a>_Required LAS Tools_  

LAS Tool | Comment
--- | ---
_las2las_ | used to extract bathy points from original tiles
_lassort_ | used to sort the bathy-only tiles by GPS time
_lassplit_ | used to split the time-sorted bathy-only tiles into separate flight line files 
_lastile_ | (if necessary) used to subtile any of the tiles that exceed number-of-data-points limits imposed in the unlicensed versions of lassort and lassplit

## Workflow  
The recommended workflow is shown in the figure below.  
![](http://web.engr.oregonstate.edu/~forfinsn/NGS_TPU_TOOL/Workflow.png)  
  
<a name="open-gui"></a>**1.  Open Gui**  
The GUI can be initiated from the command line with the following command (specify the full path of Gui.py if the current directory is not the location of Gui.py):

`python Gui.py`

NOTE:  If there are multiple Python installations on the computer running the GUI, ensure the desired installation is specified in the path environment variables or explicitly specify the full path of the relevant python executable in the command.  For example:

`C:\Python27\64-bit\python.exe Gui.py`

The GUI can also be initiated by running the Gui.py file from a Python IDE, such as IDLE or PyCharm.

<a name="data-directories"></a>**2.  Data Directories**  
The data directories can be specified in any order.  Once a directory is specified, any corresponding process button will become enabled.  For example, once the SBET Directory is specified, the _Load SBET Files_ button will become enabled.
* _LAS TOOLS BIN_:  directory containing the LAS Tool executables
* _ORIGINAL LAS TILES_:  directory containing the original las tiles generated by NGS
* _FLIGHT LINE BATHY TILES_:  directory where the time-sorted bathy-only "split" files will be generated by the Pre-Process Tiles process
* _SBET FILES_:  directory containing the SBET ASCII files

<a name="specify-parameters"></a>**3.  Specify Parameters**  

<a name="sub-aqueous-parameters"></a>  
##### Subaqueous Parameters  
The user is required to characterize two environmental conditions - the water surface and turdity.  

_Water Surface_  
The user has two options to characterize the water-surface.  Both options use pre-computed coefficient lookup tables generated using Monte Carlo simulations.  

* Riegl VQ-880-G  
This proof-of-concept option is currently limited in applicability.  The lookup tables used in this approach are generated from a water surface defined by a sampling of the first returns in a small area of the Marcos Island project.  Future development plans include deriving representative surface models for each flight line within a given tile.

* Model (ECKV spectrum)  
The lookup tables in this approach are generated using a version of the Elfouhaily et al. (ECKV) directional gravity-capillary wave spectrum model that characterizes the distribution of wave frequencies using estimates of wind speed.  

_Turbidity_  
The user is required to select a turbidity category.  Table below shows the kd(PAR?) values corresponding to each turbidity category.  

Turbidity Category | kd Range  
--- | ---  
Clear | 5-11  
Clear-Moderate | 11-18  
Moderate | 18-26  
Moderate-High | 26-33  
High | 33-41  

<a name="vertical-datum-transformation-parameters"></a>  
##### VDatum Parameters  
The user may specify a VDatum region to include that region's maximum cumulative uncertainty (MCU) in the TPU calculation.  The MCU values, obtained from _https://vdatum.noaa.gov/docs/est_uncertainties.html_, are stored in the file _V_Datum_MCU_Values.txt_.

<a name="pre-process-tiles"></a>**4.  Pre-Process Tiles**  
The _Pre-Process Tiles_ button, which calls _pre_TPU_tile_processing.py_, creates the time-sorted bathy-only tiles that are used in the TPU calculations, as illustrated in the example shown below.  The  bathy are sorted by GPS time because the merge function that matches the SBET trajectory and LAS bathymetry data requires the bathy data to be chronologically ordered.  The time-sorted files are then split into individual LAS files based on flight line.  The data are processed at the flight-line level because the polynomial-surface-fitting approach used to account for the positioning differences between the proprietary scan pattern and the implemented scan pattern assumes data to be acquired under similar conditions.  
![](http://web.engr.oregonstate.edu/~forfinsn/NGS_TPU_TOOL/PreProcessSteps.png)  
_Image Credit:  Nick Forfinski-Sarkozi_  

<a name="load-sbet-files"></a>**5.  Load SBET Files**  
The _Load SBET Files_ button, which calls _load_sbet.py_, loads the trajectory data from the ASCII SBET files in the specified SBET directory.

<a name="process-tpu"></a>**6.  Process TPU**  
The _Process TPU_ button, which calls _calc_aerial_TPU.py_, becomes enabled once the original tiles have been pre-processed and the SBET data have been loaded.

## Output  
For each input LAS tile, the TPU tool creates 2 files - a file containing TPU data and a file containing TPU metadata.  

<a name="tpu-data-file"></a>
_TPU Data File_  
The TPU data file is a comma-delimited ASCII file containing 7 fields.  The first row contains the field numbers.

Field # | Field Name | Description
--- | --- | ---
0 | easting | NAD83 (realization?) UTM easting (m)
1 | northing | NAD83 (realization?) UTM easting (m)
2 | elevation | NAVD88 elevation (m)
3 | sigmaZ_subaerial | subaerial TPU component (m)
4 | sigmaZ_subaqueous | subaqueous TPU component(m)
5 | sigmaZ_total | =sqrt(sigmaZ_subaerial^2 + sigmaZ_subaqueous^2)
6 | FILE ID | a code for the source time-sorted bathy-only flight line file (refer to the TPU metadata file)

Example TPU data file:  
```
0,1,2,3,4,5,6
431355.22,2858545.58,-26.58,0.031,0.073,0.079,0
431424.917,2858570.548,-26.614,0.031,0.073,0.079,0
431484.85,2858509.96,-26.49,0.03,0.073,0.079,1
431470.049,2858723.928,-27.129,0.03,0.073,0.079,1
431493.899,2858886.131,-26.269,0.03,0.074,0.08,1
431472.229,2858898.192,-26.297,0.03,0.073,0.079,1
431485.087,2858911.073,-26.227,0.03,0.074,0.08,1
431482.456,2858920.794,-26.186,0.03,0.074,0.08,1
431487.177,2858924.694,-26.226,0.03,0.074,0.08,1
431489.775,2858927.884,-26.086,0.03,0.074,0.08,1
431483.536,2858928.565,-26.147,0.03,0.074,0.08,1
431465.628,2858923.296,-26.336,0.03,0.073,0.079,1
431479.435,2858932.346,-26.145,0.03,0.074,0.08,1
431451.539,2858924.157,-26.382,0.03,0.073,0.079,1
431499.235,2858939.726,-26.046,0.03,0.074,0.08,1
431462.516,2858932.957,-26.283,0.03,0.073,0.079,1
431492.813,2858941.566,-25.955,0.03,0.075,0.081,1
                         :
```  

<a name="tpu-metadata-file"></a>
_TPU Metadata File_  
The TPU metadatafile contains 3 main sections:
* SUB-AQUEOUS PARAMETERS  
This section contains a record of the specified sub-aqueous parameters.  
* COMBINED SIGMA Z TPU (METERS) SUMMARY  
This section constains a statistical summary of the sigmaZ_combined values for each individual bathy-only flight line.
* FILES IDS (BATHY-ONLY FLIGHT-LINE FILES)  
This section lists the file names corresponding to the FILE ID values contained in the associated TPU data file.  

Example TPU metadata file:  
```
2016_431000e_2859000n TPU METADATA FILE

--------------------------------------------------
SUB-AQUEOUS PARAMETERS
--------------------------------------------------
water surface  :  Riegl VQ-880-G
wind           :  Light breeze (3-6 knots)
kd             :  Clear

--------------------------------------------------
COMBINED SIGMA Z TPU (METERS) SUMMARY
--------------------------------------------------
FILE ID   	MIN       	MAX       	MEAN      	STDDEV    	COUNT     
0         	0.079     	0.079     	0.079     	0.000     	2
1         	0.078     	0.084     	0.082     	0.001     	264
2         	0.080     	0.084     	0.082     	0.001     	316
3         	0.078     	0.079     	0.079     	0.001     	2
4         	0.079     	0.082     	0.080     	0.001     	317565
5         	0.079     	0.081     	0.080     	0.001     	560416
6         	0.079     	0.084     	0.082     	0.001     	621
7         	0.078     	3.041     	0.120     	0.340     	75
8         	0.078     	0.079     	0.078     	0.000     	3
9         	0.078     	0.078     	0.078     	0.000     	1
10        	0.077     	0.078     	0.078     	0.000     	29152
11        	0.078     	0.084     	0.079     	0.001     	256757
12        	0.078     	0.082     	0.079     	0.000     	699599
13        	0.078     	0.081     	0.079     	0.001     	836037

--------------------------------------------------
FILE IDS (BATHY-ONLY FLIGHT-LINE FILES)
--------------------------------------------------
0 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0000105.las
1 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0010106.las
2 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0010107.las
3 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0000106.las
4 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0010102.las
5 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0020103.las
6 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0020107.las
7 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0010105.las
8 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0010104.las
9 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0000104.las
10 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0010101.las
11 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0020106.las
12 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0020105.las
13 - I:/NGS_TPU/Data_for_TopoBathy_Lidar_TPU/TEST_DATA/SPLIT\2016_431000e_2859000n_SORTED_0020104.las
```

***

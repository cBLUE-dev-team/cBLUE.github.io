Operational Workflow
====================

The cBLUE workflow consists of 3 general steps:

1. Specify Settings

 * Data Directories
 * Environmental Parameters
 * VDatum Region
 * Configuration File Settings
	
2. Load trajectory file(s)
3. Process TPU

1. Specify Settings
###################

Currently, user-specified settings are located in the GUI and a json configuration file located in the root directory of the repository (cblue_configuration.json).  cBLUE development plans include standardizing how a user specifies settings.

Data Directories
----------------

The data directories can be specified in any order. Once a directory is specified, any corresponding process button will become enabled. For example, once the SBET Directory is specified, the Load SBET Files button will become enabled.  

Environmental Parameters
------------------------

The user is required to characterize two environmental conditions - the water surface and turbidity.  (See :ref:`environ-label` for more information.)  

VDatum Region
-------------

The user may also specify a VDatum region to include that region's maximum cumulative uncertainty (MCU) in the TPU calculation.  Currently, cBLUE assumes that all of the data points lie within one region.  cBLUE development plans include accommodating multiple regions.

Configuration File Settings
---------------------------
The configuration file contains the following settings, in addition to logging the previously saved directory settings and selected sensor model:

	* CPU processing mode (single- or multi-processing)
	* number of cores to use (if multi-processing specified)
	* cBLUE version (to be moved to a separate configuration file)
	* paths to subaqueous look up tables (LUTs) (to be moved to a separate configuration file)
	
.. warning::

	cBLUE currently requires the user to manually specify a nominal water-surface ellipsoid height for the "water_surface_ellipsoid_height" variable in the configuration file (cblue_configuration.json).  Development plans include adding the options to calculate a nominal water-suface ellipsoid height from (1) the data points classified as water surface and (2) the average separation between local mean sea level (LMSL) and the GRS80 ellipoid in the specified VDatum zone.

2. Load Trajectory File(s)
##########################
Click the *Load Trajectory File(s)* button, which loads the trajectory data from the ASCII SBET files in the specified SBET directory.

3. Process TPU
##############
Click the *Process TPU button* to calculate the TPU of all data points contained in LAS file(s) contained in the specified LAS Directory.
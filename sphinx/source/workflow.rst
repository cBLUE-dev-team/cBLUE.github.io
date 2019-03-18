Operational Workflow
====================

The recommended workflow consists of 4 steps:

1. Specify directories
2. Specify parameters
3. Load trajectory file(s)
4. Process TPU

Many of the processes within the TPU tool have status messages that are visible in either the DOS window or the IDE output window, depending on how the GUI was run. Although not always useful in production mode, these status messages may be useful when monitoring long processes or troubleshooting unintended behavior.


1. Specify Directories
######################
The data directories can be specified in any order. Once a directory is specified, any corresponding process button will become enabled. For example, once the SBET Directory is specified, the Load SBET Files button will become enabled.

2. Specify Parameters
#####################
The user is required to characterize two environmental conditions - the water surface and turdity.  The user may also specify a VDatum region to include that region's maximum cumulative uncertainty (MCU) in the TPU calculation.

3. Load Trajectory File(s)
##########################
Click the *Load Trajectory File(s)* button, which loads the trajectory data from the ASCII SBET files in the specified SBET directory.

4. Process TPU
##############
Click the *Process TPU button* to calculate the TPU of all data points contained in LAS file(s) contained in the specified LAS Directory.
Output Files
=================

cBLUE creates, in the specified Output directory, a new LAS file and metedata file for every LAS file contained in the specified LAS directory.  cBLUE also generates a processing log in the root cBLUE directory.  

LAS File (.las)
****************

The output .las file contains the same information contained in the original .las file, in addition to any of the fields listed in the following table as variable length record (VLR) extra bytes

.. raw:: html

    <style> .bold {font-weight:bold} </style>

.. role:: bold	
	
.. csv-table:: Output cBLUE Las Extra Bytes (defaults in bold)
	:header: id, dtype, description
	:widths: 14, 20, 20

	:bold:`total_thu`,  :bold:`unsigned short (1 byte)`, :bold:`total horizontal uncertainty`
	:bold:`total_tvu`,  :bold:`unsigned short (1 byte)`, :bold:`total vertical uncertainty`
	cblue_x, unsigned long long (8 bytes), cBLUE-calculated x coordinate
	cblue_y, unsigned long long (8 bytes), cBLUE-calculated y coordinate
	cblue_z, long (4 bytes), cBLUE-calculated z coordinate
	subaerial_thu, unsigned short (1 byte), subaerial total horizontal uncertainty
	subaerial_tvu, unsigned short (1 byte), subaerial total vertical uncertainty
	subaqueous_thu, unsigned short (1 byte), subaqueous total horizontal uncertainty
	subaqueous_tvu, unsigned short (1 byte), subaqueous total vertical uncertainty

By default, the only the total propagated horizontal uncertainty (THU) and total propagated vertical uncertainty (TVU) are exported as extra bytes.  The cBLUE-calculated position and subaerial/subaqueous component TPU fields can be exported as extra bytes by uncommenting the corresponding lines of code in the output_tpu_to_las_extra_bytes method of the TPU class.  	
	
.. warning::

	Exporting non-default fields is not aligned with current draft standard ExtraByte definitions of the ASPRS Las Working Group (https://github.com/ASPRSorg/LAS/wiki/Standard-ExtraByte-Definitions).  Additionally, exporting addition extra bytes will increase file sizes and processing times.
	
Metadata File (.json)
*********************

The .json metadata file contains the following information:

* cBLUE version
* Sensor model
* per flight line summary statistics of component an total THU and TVU
* VDatum region and corresponding region MCU
* Environmental parameters (including subaqueous lookup parameters)
* CPU processing information (single- or multi-processing)

cBLUE log
*********

By default, cBLUE is configured to export messages with a logging level of INFO and above to a text log file in cBLUE's root directory.

.. warning::

	The log file was originally intended for single-processing.  The log file for multi-processing currently does not necessarily log all intended messages.  Development plans include reworking log-file generation to accommodate logging messages from multiple processes to a single file.


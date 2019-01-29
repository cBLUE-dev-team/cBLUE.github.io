Output Files
=================

cBLUE creates, in the specifeid Output directory, a new LAS file and metedata file for every LAS file contained in the specified LAS directory:

LAS File (.las)
****************
The output .las file contains the data described in the following table as VLR extra bytes, along with the contents of the original .las file.

.. note::

	The scale associated with the VLR extra bytes is 0.001, which is NOT necessarily the same as the scale value specified in the las header (typically 0.01).  THIS IS NOT STANDARD IN THE LAS COMMUNITY.  The ASPRS Las Working Group has an active conversation regarding how to standardized the use of extra bytes for supplementary fields such as uncertainty (https://github.com/ASPRSorg/LAS/issues/37).

.. csv-table:: Output cBLUE Data
	:header: id, dtype, description
	:widths: 14, 20, 20

	cblue_x, unsigned long long (8 bytes), cBLUE-calculated x coordinate
	cblue_y, unsigned long long (8 bytes), cBLUE-calculated y coordinate
	cblue_z, long (4 bytes), cBLUE-calculated z coordinate
	subaerial_thu, unsigned short (2 bytes), subaerial total horizontal uncertainty
	subaerial_tvu, unsigned short (2 bytes), subaerial total vertical uncertainty
	subaqueous_thu, unsigned short (2 bytes), subaqueous total horizontal uncertainty
	subaqueous_tvu, unsigned short (2 bytes), subaqueous total vertical uncertainty
	total_thu,  unsigned short (2 bytes), total horizontal uncertainty
	total_tvu,  unsigned short (2 bytes), total vertical uncertainty

Metadata File (.json)
*********************
The .json metadata file contains the following information:


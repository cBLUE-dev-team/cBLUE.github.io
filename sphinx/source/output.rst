Output Files
=================

cBLUE creates, in the specifeid Output directory, a new LAS file and metedata file for every LAS file contained in the specified LAS directory:

LAS File (.las)
****************
The output .las file contains the data desribed in the following table as VLR extra bytes, along with the contents of the original .las file.

.. note::

	The scale associated with the VLR extra bytes is the same as the (typeically 0.01).  To convert the VLR extra bytes data into 

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
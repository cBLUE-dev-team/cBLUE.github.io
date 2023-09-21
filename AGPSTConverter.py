"""
cBLUE (comprehensive Bathymetric Lidar Uncertainty Estimator)
Copyright (C) 2019
Oregon State University (OSU)
Center for Coastal and Ocean Mapping/Joint Hydrographic Center, University of New Hampshire (CCOM/JHC, UNH)
NOAA Remote Sensing Division (NOAA RSD)

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

Contact:
Christopher Parrish, PhD
School of Construction and Civil Engineering
101 Kearney Hall
Oregon State University
Corvallis, OR  97331
(541) 737-5688
christopher.parrish@oregonstate.edu

Last Edited By:
Keana Kief (OSU)
August 23th, 2023

"""
from datetime import datetime, timezone

# Adjusted GPS Time Converter for cBLUE


def convert_to_agpst(sbet_date, fl_las_time_data):
    """
    This function returns the las time data converted to Adjusted Standard GPS time. 

    convert_to_AGPST takes in the date that the data was collected from the title of the sbet file, and the 1d array of time data from the Las file.

    The the first values of the las time data is tested to see if it is in UTC, GPS, or Adjusted Standart GPS time. 

    If it is already in Adjusted Standard GPS time, return the time data unchanged. If the Las data is in UTC or GPS, the time data is converted to
        Adjusted Standard GPS time and the adjusted time array is returned. 

    Parameters: 
    sbet_date - [year, month, day] ex. [2023,8,23] for August, 23rd, 2023
    fl_las_time_data - 1d column array of the las time values

    Returns: 
    adjusted_fl_las_time_data - 1d column array of the las time data in Adjusted Standard GPS Time. Only if the fl_las_time_data was in GPS or UTC time.
    fl_las_time_data - 1d column array of the las time values. Only if fl_las_time_data was already in Adjusted Standard GPS Time. 
    """

    #Check if the las data is already in Adjusted Standard GPS time. 
    if(is_agps_time(sbet_date, fl_las_time_data[0])):
        #If it is, return the data unchanged
        return fl_las_time_data


def is_gps_time(sbet_date, fl_las_time_data_sample):

def is_utc_time(sbet_date, fl_las_time_data_sample):

def is_agps_time(sbet_date, fl_las_time_data_sample):
    """
    Checks if the timestamp sample from the las data is in Adjusted Standard GPS time.

    Returns true if the timestamp is in Adjusted Standard GPS time, and false otherwise. 
    """



def convert_utc_to_agps(fl_las_time_data):

def get_leap_seconds():

def get_utc_timestamp_range(sbet_date):
    """
    Takes in an sbet_date array holding the [Year, Month, Day] and returns a tuple with the UTC timestamps for
    the beginning of the day (00:00:00) and the end of the day (23:59:59).

    Parameter: 
    sbet_date - [year, month, day] ex. [2023,8,23] for August, 23rd, 2023
    """






if __name__ == "__main__":
    pass
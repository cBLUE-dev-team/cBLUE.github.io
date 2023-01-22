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

"""
import os


class Datum:
    def __init__(self):
        pass

    def get_vdatum_region_mcus(self):
        vdatum_regions_MCU_file = os.path.join(
            "lookup_tables", "V_Datum_MCU_Values.txt"
        )
        with open(vdatum_regions_MCU_file, "r") as vdatum_regions_file_obj:
            vdatum_regions = vdatum_regions_file_obj.readlines()

        # clean up vdatum file; when copying table from internet, some dashes
        # are 'regular dashes' and others are \x96; get rid of quotes and \n
        default_msg = "---No Region Specified---"
        vdatum_regions = [v.replace("\x96", "-") for v in vdatum_regions]
        vdatum_regions = [v.replace('"', "") for v in vdatum_regions]
        vdatum_regions = [v.replace("\n", "") for v in vdatum_regions]
        regions = [v.split("\t")[0] for v in vdatum_regions]
        mcu_values = [v.split("\t")[1] for v in vdatum_regions]

        return regions, mcu_values, default_msg

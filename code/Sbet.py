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
import time
import pandas as pd
from datetime import datetime
import progressbar
from .sbet_utils import get_date, sow_to_adj, read_sbet
import logging

logger = logging.getLogger(__name__)

"""
This class provides the functionality to load trajectory data into
cBLUE.  Currently, the sbet files are expected to be ASCII files
that are exported from Applanix's PosPac software.
"""


class Sbet:
    def __init__(self, sbet_dir):
        """
        The data from all of the loaded sbet files are represented by
        a single Sbet object.  When the Sbet class is instantiated,
        the sbet object does not contain any sbet data.  The data
        are "loaded" (assigned to a field of the sbet object) when
        the user clicks the 'Load Sbet Data' button.
        :param str sbet_dir: directory contained trajectory files
        """

        # Directory of sbet trajectory files (from GUI)
        self.sbet_dir = sbet_dir

        # Get list of sbet files (.txt's)
        self.sbet_files = sorted(
            [
                os.path.join(sbet_dir, f)
                for f in os.listdir(sbet_dir)
                if f.endswith(".txt")
            ]
        )

    def build_sbets_data(self):
        """builds 1 pandas dataframe from all ASCII sbet files

        :return: pandas dataframe

        The following table lists the contents of the returned pandas sbet dataframe:

        =====   =============================================================
        Index   description
        =====   =============================================================
        0       timestamp (GPS seconds-of-week or GPS standard adjusted time)
        1       longitude
        2       latitude
        3       X (easting)
        4       Y (northing)
        5       Z (ellipsoid height)
        6       roll
        7       pitch
        8       heading
        9       standard deviation X
        10      standard deviation Y
        11      standard deviation Z
        12      standard deviation roll
        13      standard deviation pitch
        14      standard deviation heading
        =====   =============================================================
        """

        print(r"Loading trajectory files...")
        logger.sbet(f"loading {len(self.sbet_files)} trajectory files...")

        sbets_df = pd.concat(
            [
                read_sbet(fname)
                for fname in progressbar.progressbar(
                    sorted(self.sbet_files), redirect_stdout=True
                )
            ]
        )

        sbets_data = sbets_df.sort_values(["time"], ascending=True)

        return sbets_data

    def set_data(self):
        """populates Sbet object's data field with pandas dataframe (when user
        presses the "Load Trajectory File(s)" button)

        THIS FUNCTION HAS ONE ACTIONABLE LINE OF CODE - CUT IT!!!

        :return: n/a
        """

        sbet_tic = time.process_time()

        # This is the only line that matters!!!
        self.data = self.build_sbets_data()  # df

        # Who cares how long it took? (not me!)
        sbet_toc = time.process_time()
        logger.sbet(
            "It took {:.1f} mins to load the trajectory data.".format(
                (sbet_toc - sbet_tic) / 60
            )
        )

    def get_tile_data(self, north, south, east, west):
        """queries the sbet data points that lie within the given las tile bounding coordinates

        One pandas dataframe is created from all of the loaded ASCII sbet files,
        but as each las tile is processed, only the sbet data located within the
        las tile limits are sent to the calc_tpu() method.

        To account for las tiles that contain data points from a las flight line
        whose corresponding trajectory data falls outside of the las tile extents,
        a buffer is added to the bounds of the tile when retreiving the
        trajectory data.

        :param float north: northern limit of las tile
        :param float south: southern limit of las tile
        :param float east: eastern limit of las tile
        :param float west: western limit of las tile
        :return: pandas dataframe
        """

        buff = 500  # meters

        x = self.data.X.values
        y = self.data.Y.values

        north += buff
        south -= buff
        east += buff
        west -= buff

        data = self.data[(y >= south) & (y <= north) & (x >= west) & (x <= east)]

        return data

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
import logging

logger = logging.getLogger(__name__)

"""
This class provides the functionality to load trajectory data into
cBLUE.  Currently, the sbet files are expected to be ASCII files
that are exported from Applanix's PosPac software.
"""

# Static Globals
SECS_PER_GPS_WK = 7 * 24 * 60 * 60  # 604800 sec
SECS_PER_DAY = 24 * 60 * 60  # 86400 sec
GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)
GPS_ADJUSTED_OFFSET = 1e9


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

    @staticmethod
    def get_sbet_date(sbet):
        """parses year, month, and day from ASCII sbet filename

        :param str sbet: ASCII sbet filename
        :return: List[int]
        """
        # normalize path and split on dir seperator
        sbet_path = os.path.normpath(sbet)
        sbet_parts = os.path.split(sbet_path)

        sbet_name = sbet_parts[-1]
        logger.sbet(f"SBET Name : {sbet_name}")

        # Sbet date embedded in file name by convention
        year = int(sbet_name[0:4])
        month = int(sbet_name[4:6])
        day = int(sbet_name[6:8])
        return (year, month, day)

    def gps_sow_to_gps_adj(self, gps_date, gps_wk_sec):
        """converts GPS seconds-of-week timestamp to GPS adjusted standard time

        In the case that the timestamps in the sbet files are GPS week seconds,
        this method is called to convert the timestamps to GPS adjusted standard
        time, which is what the las file timestamps are.  The timestamps in the
        sbet and las files need to be the same format, because the merging process
        merges the data in the sbet and las files based on timestamps.

        :param ? gps_date: (year, month, day)
        :param ? gps_wk_sec: GPS seconds-of-week timestamp
        :return: float
        """

        logger.sbet("converting GPS week seconds to GPS adjusted standard time..."),

        dt = datetime(*gps_date) - GPS_EPOCH
        gps_wk = int((dt.days * SECS_PER_DAY + dt.seconds) / SECS_PER_GPS_WK)
        gps_time = gps_wk * SECS_PER_GPS_WK + gps_wk_sec
        gps_time_adj = gps_time - GPS_ADJUSTED_OFFSET

        return gps_time_adj

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

        # Define sbet column headers
        header_sbet = [
            "time",
            "lon",
            "lat",
            "X",
            "Y",
            "Z",
            "roll",
            "pitch",
            "heading",
            "stdX",
            "stdY",
            "stdZ",
            "stdroll",
            "stdpitch",
            "stdheading",
        ]

        print(r"Loading trajectory files...")
        logger.sbet(f"loading {len(self.sbet_files)} trajectory files...")

        # Set up dataframe to hold all trajectories from sbet files
        sbets_df = pd.DataFrame()
        for sbet in progressbar.progressbar(
            sorted(self.sbet_files), redirect_stdout=True
        ):
            logger.sbet("-" * 50)
            logger.sbet(f"{os.path.split(sbet)[-1]}...")

            # Load sbet trajectories
            sbet_df = pd.read_csv(
                sbet,
                delim_whitespace=True,
                header=None,
                names=header_sbet,
            )

            logger.sbet("({} trajectory points)".format(sbet_df.shape[0]))
            sbet_date = self.get_sbet_date(sbet)

            # Check GPS time format for week seconds
            logger.sbet("checking if timestamps are GPS week seconds...")
            if sbet_df["time"][0] <= SECS_PER_GPS_WK:
                # Reset time to adjusted standard time
                sbet_df["time"] = self.gps_sow_to_gps_adj(sbet_date, sbet_df["time"])

            # Append the sbet to the full trajectory dataframe
            sbets_df = sbets_df.append(sbet_df, ignore_index=True)

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

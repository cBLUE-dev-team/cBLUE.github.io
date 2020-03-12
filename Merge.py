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

import numpy as np
import numexpr as ne
from math import radians
import logging


class Merge:

    max_allowable_dt = 1.0  # second

    def __init__(self):
        self.a_std_dev = 0.02  # degrees
        self.b_std_dev = 0.02  # degrees
        self.std_rho = 0.025

        """returns sbet & las data merged based on timestamps

        The cBLUE TPU calculations require the sbet and las data to be in
        a single array, so the sbet and lidar data, which are contained in
        separate files, are 'merged', based on time.  cBLUE uses the numpy
        searchsorted function to match lidar datapoints with the nearest-in-time
        (with sorter='left') sbet datapoints.

        If the delta_t between any of the matched datapoints is > 1, TPU is
        not calculated.  Future versions might be smart enough to exclude only
        the offending datapoints rather than discarding the whole file, but for
        the time being, if a single datapoint's delta_t exceeds the allowable
        maximum dt, the entire line is ignored.

        :param str las:
        :param ? fl:
        :param ? sbet_data:
        :param Tuple(ndarray)  # TODO: are the parentheses necessary?
        :return: List[ndarray]

        The following table lists the contents of the returned list of ndarrays:

        =====   =========   ========================    =======
        Index   ndarray     description                 units
        =====   =========   ========================    =======
        0       t_sbet      sbet timestamps
        1       t_las       las timestamps
        2       x_las       las x coordinates
        3       y_las       las y coordinates
        4       z_las       las z coordinates
        5       x_sbet      sbet x coordinates
        6       y_sbet      sbet y coordinates
        7       z_sbet      sbet z coordinates
        8       r           sbet roll
        9       p           sbet pitch
        10      h           sbet heading
        11      std_a       a uncertainty
        12      std_b       b uncertainty
        13      std_r       sbet roll uncertainty
        14      std_p       sbet pitch uncertainty
        15      std_h       sbet heading uncertainty
        16      stdx_sbet   sbet x uncertainty
        17      stdy_sbet   sbet y uncertainty
        18      stdz_sbet   sbet z uncertainty
        =====   =========   ========================    =======
        """

    def merge(self, las, fl, sbet_data, fl_unsorted_las_xyzt, fl_t_argsort, fl_las_idx):

        num_sbet_pts = sbet_data.shape[0]

        # sort xyzt array based on t_idx column
        idx = fl_t_argsort.argsort()
        fl_las_data = fl_unsorted_las_xyzt[idx]
        fl_las_idx = fl_las_idx[idx]

        # match sbet and las dfs based on timestamps
        idx = np.searchsorted(sbet_data[:, 0], fl_las_data[:, 3])

        # don't use las points outside range of sbet points
        mask = ne.evaluate('0 < idx') & ne.evaluate('idx < num_sbet_pts')

        t_sbet_masked = sbet_data[:, 0][idx[mask]]
        t_las_masked = fl_las_data[:, 3][mask]

        dt = ne.evaluate('t_sbet_masked - t_las_masked')
        max_dt = ne.evaluate('max(dt)')  # may be empty

        if max_dt > self.max_allowable_dt or max_dt.size == 0:
            data = False
            stddev = False
            raw_class = False

            logging.warning('trajectory and LAS data NOT MERGED')
            logging.warning('({} FL {}) max_dt: {}'.format(las, fl, max_dt))
        else:
            data = np.asarray([
                sbet_data[:, 0][idx[mask]],                     # t?
                fl_las_data[:, 3][mask],                        # t
                fl_las_data[:, 0][mask],                        # x
                fl_las_data[:, 1][mask],                        # y
                fl_las_data[:, 2][mask],                        # z
                sbet_data[:, 3][idx[mask]],                     # x?
                sbet_data[:, 4][idx[mask]],                     # y?
                sbet_data[:, 5][idx[mask]],                     # z?
                np.radians(sbet_data[:, 6][idx[mask]]),         # r?
                np.radians(sbet_data[:, 7][idx[mask]]),         # p?
                np.radians(sbet_data[:, 8][idx[mask]])          # h?
            ])

            num_points = data[0].shape

            stddev = np.vstack([
                np.full(num_points, radians(self.a_std_dev)),   # std_a
                np.full(num_points, radians(self.b_std_dev)),   # std_b
                np.radians(sbet_data[:, 12][idx[mask]]),        # std_r
                np.radians(sbet_data[:, 13][idx[mask]]),        # std_p
                np.radians(sbet_data[:, 14][idx[mask]]),        # std_h
                sbet_data[:, 9][idx[mask]],                     # stdx_sbet
                sbet_data[:, 10][idx[mask]],                    # stdy_sbet
                sbet_data[:, 11][idx[mask]],                    # stdz_sbet
                np.full(num_points, self.std_rho)               # std_rho
            ])

            raw_class = fl_las_data[:, 4][mask]

        return data, stddev, fl_las_idx[mask], raw_class  # 2nd to last array is masked t_idx


if __name__ == '__main__':
    pass

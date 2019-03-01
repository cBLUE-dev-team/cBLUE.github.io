import numpy as np
import numexpr as ne
import logging
from math import radians


class Merge:

    def __init__(self, las, fl, sbet_data, (las_t, las_x, las_y, las_z)):
        self.las = las
        self.fl = fl
        self.sbet_data = sbet_data
        self.las_t = las_t
        self.las_x = las_x
        self.las_y = las_y
        self.las_z = las_z

        self.a_std_dev = 0.02  # degrees
        self.b_std_dev = 0.02  # degrees
        self.std_rho = 0.025
        self.max_allowable_dt = 1.0

        self.data = self.merge()

    def merge(self):
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

        =====   =========   =======================
        Index   ndarray     description
        =====   =========   =======================
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
        19      std_rho     ?
        =====   =========   =======================
        """

        # match sbet and las dfs based on timestamps
        sbet_t = self.sbet_data[:, 0]
        num_chunk_points = self.las_t.shape
        idx = np.searchsorted(self.sbet_t, self.las_t) - 1
        mask = ne.evaluate('idx >= 0')

        dt = self.las_t[mask] - self.sbet_data[:, 0][idx][mask]
        max_dt = np.max(dt)
        logging.info('({} FL {}) max_dt: {}'.format(las, fl, max_dt))

        if max_dt > self.max_allowable_dt:
            merged_data = []
        else:
            merged_data = np.array([
                self.sbet_data[:, 0][idx][mask],                        # [0] t_sbet
                self.las_t[mask],                                       # [1] t_las
                self.las_x[mask],                                       # [2] x_las
                self.las_y[mask],                                       # [3] y_las
                self.las_z[mask],                                       # [4] z_las
                self.sbet_data[:, 3][idx][mask],                        # [5] x_sbet
                self.sbet_data[:, 4][idx][mask],                        # [6] y_sbet
                self.sbet_data[:, 5][idx][mask],                        # [7] z_sbet
                np.radians(sbet_data[:, 6][idx][mask]),                 # [8] r
                np.radians(sbet_data[:, 7][idx][mask]),                 # [9] p
                np.radians(sbet_data[:, 8][idx][mask]),                 # [10] h
                np.full(num_chunk_points, radians(self.a_std_dev)),     # [11] std_a
                np.full(num_chunk_points, radians(self.b_std_dev)),     # [12] std_b
                np.radians(sbet_data[:, 12][idx][mask]),                # [13] std_r
                np.radians(sbet_data[:, 13][idx][mask]),                # [14] std_p
                np.radians(sbet_data[:, 14][idx][mask]),                # [15] std_h
                self.sbet_data[:, 9][idx][mask],                        # [16] stdx_sbet
                self.sbet_data[:, 10][idx][mask],                       # [17] stdy_sbet
                self.sbet_data[:, 11][idx][mask],                       # [18] stdz_sbet
                np.full(num_chunk_points, self.std_rho)])               # [19] std_rho

            names = 't_sbet, t_las, \
            x_las, y_las, z_las, \
            x_sbet, y_sbet, z_sbet, \
            r, p, h, \
            std_a, std_b, \
            std_r, std_p, std_h, \
            stdx_sbet, stdy_sbet, stdz_sbet, \
            std_rho'

            formats = ','.join(['f8'] * len(names))

        return np.core.records.fromarrays(merged_data, names=names, formats=formats)


if __name__ == '__main__':
    pass

import numpy as np
import numexpr as ne
import logging
from math import radians


class Merge:

    def __init__(self, las, fl, sbet_data, (las_t, las_x, las_y, las_z)):

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

        =====   =========   ========================
        Index   ndarray     description
        =====   =========   ========================
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
        =====   =========   ========================
        """

        self.a_std_dev = 0.02  # degrees
        self.b_std_dev = 0.02  # degrees
        self.std_rho = 0.025
        self.max_allowable_dt = 1.0

        # match sbet and las dfs based on timestamps
        # sbet_data[:, 0] = sbet_t
        idx = np.searchsorted(sbet_data[:, 0], las_t) #- 1
        mask = ne.evaluate('idx >= 0')

        dt = las_t[mask] - sbet_data[:, 0][idx][mask]
        max_dt = np.max(dt)
        logging.info('({} FL {}) max_dt: {}'.format(las, fl, max_dt))

        if max_dt > self.max_allowable_dt:
            self.num_points = 0
        else:
            self.t_sbet = sbet_data[:, 0][idx][mask]
            self.t_las = las_t[mask]
            self.x_las = las_x[mask]
            self.y_las = las_y[mask]
            self.z_las = las_z[mask]
            self.x_sbet = sbet_data[:, 3][idx][mask]
            self.y_sbet = sbet_data[:, 4][idx][mask]
            self.z_sbet = sbet_data[:, 5][idx][mask]
            self.r = np.radians(sbet_data[:, 6][idx][mask])
            self.p = np.radians(sbet_data[:, 7][idx][mask])
            self.h = np.radians(sbet_data[:, 8][idx][mask])

            self.num_points = self.t_sbet.size

            self.stddev = np.array([
                np.full(self.num_points, radians(self.a_std_dev)),      # std_a
                np.full(self.num_points, radians(self.b_std_dev)),      # std_b
                np.radians(sbet_data[:, 12][idx][mask]),                # std_r
                np.radians(sbet_data[:, 13][idx][mask]),                # std_p
                np.radians(sbet_data[:, 14][idx][mask]),                # std_h
                sbet_data[:, 9][idx][mask],                             # stdx_sbet
                sbet_data[:, 10][idx][mask],                            # stdy_sbet
                sbet_data[:, 11][idx][mask],                            # stdz_sbet
                np.full(self.num_points, self.std_rho)])                # std_rho


if __name__ == '__main__':
    pass

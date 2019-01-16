import numpy as np
import numexpr as ne
import logging
from math import radians


class Merge:
    dt_threshold = 1  # seconds

    def __init__(self):
        pass

    @staticmethod
    def merge(las, fl, sbet_data, (las_t, las_x, las_y, las_z)):
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
        11      std_ang1    ang1 uncertainty
        12      std_ang2    ang2 uncertainty
        13      std_r       sbet roll uncertainty
        14      std_p       sbet pitch uncertainty
        15      std_h       sbet heading uncertainty
        16      stdx_sbet   sbet x uncertainty
        17      stdy_sbet   sbet y uncertainty
        18      stdz_sbet   sbet z uncertainty
        19      std_rho     ?
        =====   =========   =======================
        """

        a_std_dev = 0.02  # degrees
        b_std_dev = 0.02  # degrees
        std_rho = 0.025
        max_allowable_dt = 1.0

        # match sbet and las dfs based on timestamps
        sbet_t = sbet_data[:, 0]
        num_chunk_points = las_t.shape
        idx = np.searchsorted(sbet_t, las_t) - 1
        mask = ne.evaluate('idx >= 0')

        dt = las_t[mask] - sbet_data[:, 0][idx][mask]
        max_dt = np.max(dt)
        logging.info('({} FL {}) max_dt: {}'.format(las, fl, max_dt))

        if max_dt > max_allowable_dt:
            merged_data = []
        else:
            merged_data = [
                sbet_data[:, 0][idx][mask],  # t_sbet
                las_t[mask],  # t_las
                las_x[mask],  # x_las
                las_y[mask],  # y_las
                las_z[mask],  # z_las
                sbet_data[:, 3][idx][mask],  # x_sbet
                sbet_data[:, 4][idx][mask],  # y_sbet
                sbet_data[:, 5][idx][mask],  # z_sbet
                np.radians(sbet_data[:, 6][idx][mask]),  # r
                np.radians(sbet_data[:, 7][idx][mask]),  # p
                np.radians(sbet_data[:, 8][idx][mask]),  # h
                np.full(num_chunk_points, radians(a_std_dev)),  # std_ang1
                np.full(num_chunk_points, radians(b_std_dev)),  # std_ang2
                np.radians(sbet_data[:, 12][idx][mask]),  # std_r
                np.radians(sbet_data[:, 13][idx][mask]),  # std_p
                np.radians(sbet_data[:, 14][idx][mask]),  # std_h
                sbet_data[:, 9][idx][mask],  # stdx_sbet
                sbet_data[:, 10][idx][mask],  # stdy_sbet
                sbet_data[:, 11][idx][mask],  # stdz_sbet
                np.full(num_chunk_points, std_rho)]  # std_rho

        return merged_data


if __name__ == '__main__':
    pass

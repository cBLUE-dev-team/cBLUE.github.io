import numpy as np
import numexpr as ne
import logging
from math import radians


class Merge:
    dt_threshold = 1  # seconds

    def __init__(self):
        pass

    # match up las and sbet data using timestamps
    def merge(sbet_data, las_t, las_x, las_y, las_z):

        a_std_dev = 0.02  # degrees
        b_std_dev = 0.02  # degrees

        # match sbet and las dfs based on timestamps
        sbet_t = sbet_data[:, 0]
        num_chunk_points = las_t.shape
        idx = np.searchsorted(sbet_t, las_t) - 1
        mask = ne.evaluate('idx >= 0')

        dt = las_t[mask] - sbet_data[:, 0][idx][mask]
        max_dt = np.max(dt)

        logging.info('max_dt: {}'.format(max_dt))

        if max_dt > 1:
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
                np.full(num_chunk_points, 0.025)]  # std_rho

        return merged_data


if __name__ == '__main__':
    pass

# -*- coding: utf-8 -*-

import numpy as np
import json


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated Gui.py.
    """

    def __init__(self):
        pass

    @staticmethod
    def main(surface, wind_par, kd_par, depth):
        """Called to begin the SubAqueous processing.

        @return   res        float[]   (SubAqueous TPU)
        """
        if surface == 0:
            fit_tvu = Subaqueous.riegl_process(kd_par)
        else:
            fit_thu, fit_tvu = Subaqueous.model_process(wind_par, kd_par)

        res_tvu = fit_tvu[0] * depth ** 2 + fit_tvu[1] * depth+fit_tvu[2]
        res_thu = fit_thu[0] * depth ** 2 + fit_thu[1] * depth+fit_thu[2]

        columns = ['subaqueous_thu', 'subaqueous_tvu']

        return res_thu.T, res_tvu.T, columns

    @staticmethod
    def model_process(wind, kd):
        """Retrieves the average fit for all given combinations of wind and kd given from look_up_fit.csv.
        look_up_fit.csv uses precalculated uncertainties based on seasurface models.

        @param    wind   int[]     (possible wind values as determined by the GUI)
        @param    kd     int[]     (possible turbidity levels as determined by the GUI)

        @return   fit    float[]   (polynomial fit for SubAqueous TPU)
        """

        look_up_tvu = open("ECKV_look_up_fit_HG0995_1sig.csv")
        look_up_tvu_data = look_up_tvu.readlines()
        look_up_tvu.close()
        fit_tvu = np.asarray([0.0, 0.0, 0.0])

        look_up_thu = open("THU.csv")
        look_up_thu_data = look_up_thu.readlines()
        look_up_thu.close()
        fit_thu = np.asarray([0.0, 0.0, 0.0])

        for w in wind:
            for k in kd:
                fit_par_tvu_strings = look_up_tvu_data[31 * (w - 1) + k - 6].split(",")[:-1]  # exclude trailing \n
                fit_par_tvu = np.asarray(fit_par_tvu_strings).astype(np.float64)
                fit_tvu += fit_par_tvu  # adding two 3-element arrays

                fit_par_thu_strings = look_up_thu_data[31 * (w - 1) + k - 6].split(",")[:-1]  # exclude trailing \n
                fit_par_thu = np.asarray(fit_par_thu_strings).astype(np.float64)
                fit_thu += fit_par_thu  # adding two 3-element arrays

        fit_tvu /= len(kd)*len(wind)
        fit_thu /= len(kd)*len(wind)

        return fit_thu, fit_tvu

    @staticmethod
    def riegl_process(kd):
        """Retrieves the average fit for all kd given from reigl_look_up_fit.csv.
        reigl_look_up_fit.csv uses precalculated uncertainties based on riegl models.

        @param    kd     int[]     (possible turbidity levels as determined by the GUI)

        @return   fit    float[]   (polynomial fit for SubAqueous TPU)
        """

        look_up = open("Riegl_look_up_fit_HG0995_1sig.csv")
        look_up_data = look_up.readlines()
        look_up.close()
        fit = np.asarray([0, 0, 0])
        for k in kd:
            fit_par_str = look_up_data[k-6].split(",")
            fit_par = np.asarray(fit_par_str)[:-1].astype(np.float64)
            fit += fit_par  # adding two 3-element arrays

        fit /= len(kd)

        return fit

    @staticmethod
    def get_subaqueous_meta_data(f):
        subaqueous_f = open(f, 'r')
        subaqueous_metadata = subaqueous_f.readline().split(',')
        subaqueous_metadata = {k: v.strip() for (k, v) in [n.split(':') for n in subaqueous_metadata]}
        return subaqueous_metadata


if __name__ == '__main__':
    pass

# -*- coding: utf-8 -*-

import numpy as np


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated Gui.py.

    Created on 2017-12-11

    @author: Timothy Kammerer
    """

    def __init__(self):
        pass

    @staticmethod
    def main(surface, wind_par, kd_par, depth):
        """Called to begin the SubAqueous processing.

        @param    surface    int       (Type of surface generation)   0=riegl 1=model
        @param    wind_par   int[]     (possible wind values as determined by the GUI)
        @param    kd_par     int[]     (possible turbidity levels as determined by the GUI)
        @param    depth      float[]   (Depth of the points, for which TPU will be determined)

        @return   res        float[]   (SubAqueous TPU)
        """
        if surface == 0:
            fit = Subaqueous.riegl_process(kd_par)
        else:
            fit = Subaqueous.model_process(wind_par, kd_par)

        res = fit[0]*depth**2+fit[1]*depth+fit[2]

        columns = ['subaqueous_sz']

        return np.asarray(res).T, columns

    @staticmethod
    def model_process(wind, kd):
        """Retrieves the average fit for all given combinations of wind and kd given from look_up_fit.csv.
        look_up_fit.csv uses precalculated uncertainties based on seasurface models.

        @param    wind   int[]     (possible wind values as determined by the GUI)
        @param    kd     int[]     (possible turbidity levels as determined by the GUI)

        @return   fit    float[]   (polynomial fit for SubAqueous TPU)
        """

        look_up = open("ECKV_look_up_fit_HG0995_1sig_JALBTCX_temp.csv")
        look_up_data = look_up.readlines()
        look_up.close()
        fit = [0, 0, 0]
        for w in wind:
            for k in kd:
                fit_par = look_up_data[31*(w-1)+k-6].split(",")
                fit[0] += float(fit_par[0])
                fit[1] += float(fit_par[1])
                fit[2] += float(fit_par[2])
        fit[0] /= len(kd)*len(wind)
        fit[1] /= len(kd)*len(wind)
        fit[2] /= len(kd)*len(wind)
        return fit

    @staticmethod
    def riegl_process(self, kd):
        """Retrieves the average fit for all kd given from reigl_look_up_fit.csv.
        reigl_look_up_fit.csv uses precalculated uncertainties based on riegl models.

        @param    kd     int[]     (possible turbidity levels as determined by the GUI)

        @return   fit    float[]   (polynomial fit for SubAqueous TPU)
        """

        look_up = open("Riegl_look_up_fit_HG0995_1sig.csv")
        look_up_data = look_up.readlines()
        look_up.close()
        fit = [0, 0, 0]
        for k in kd:
            fit_par = look_up_data[k-6].split(",")
            fit[0] += float(fit_par[0])
            fit[1] += float(fit_par[1])
            fit[2] += float(fit_par[2])
        fit[0] /= len(kd)
        fit[1] /= len(kd)
        fit[2] /= len(kd)
        return fit

    @staticmethod
    def get_subaqueous_meta_data(f):
        subaqueous_f = open(f, 'r')
        subaqueous_metadata = subaqueous_f.readline().split(',')
        subaqueous_metadata = {k: v.strip() for (k, v) in [n.split(':') for n in subaqueous_metadata]}
        return subaqueous_metadata


if __name__ == '__main__':
    pass

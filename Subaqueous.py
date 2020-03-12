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

# -*- coding: utf-8 -*-

import numpy as np


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated Gui.py.
    """

    def __init__(self, surface, wind_par, kd_par, depth, subaqueous_luts):
        self.surface = surface
        self.wind_par = wind_par
        self.kd_par = kd_par
        self.depth = depth
        self.subaqueous_luts = subaqueous_luts
        self.curr_lut = None
        self.thu = None
        self.tvu = None

    def fit_lut(self):
        """Called to begin the SubAqueous processing.
        """

        if self.surface == 0:
            self.curr_lut = self.subaqueous_luts['Reigl']
            fit_tvu = self.riegl_process(self.curr_lut)
        else:
            self.curr_lut = self.subaqueous_luts['ECKV']
            fit_thu, fit_tvu = self.model_process(self.curr_lut)

        res_thu = fit_thu[0] * self.depth ** 2 + fit_thu[1] * self.depth + fit_thu[2]
        res_tvu = fit_tvu[0] * self.depth ** 2 + fit_tvu[1] * self.depth + fit_tvu[2]

        self.thu = res_thu.T
        self.tvu = res_tvu.T

        return self.thu, self.tvu

    def model_process(self, lut):
        """Retrieves the average fit for all given combinations of wind and kd given from look_up_fit.csv.
        look_up_fit.csv uses precalculated uncertainties based on seasurface models.
        """

        look_up_tvu = open(lut)
        look_up_tvu_data = look_up_tvu.readlines()
        look_up_tvu.close()
        fit_tvu = np.asarray([0.0, 0.0, 0.0])

        look_up_thu = open("./lookup_tables/THU.csv")
        look_up_thu_data = look_up_thu.readlines()
        look_up_thu.close()
        fit_thu = np.asarray([0.0, 0.0, 0.0])

        # TODO:  what are '31' and '6' in following equations?

        for w in self.wind_par:
            for k in self.kd_par:
                fit_par_tvu_strings = look_up_tvu_data[31 * (w - 1) + k - 6].split(",")[:-1]  # exclude trailing \n
                fit_par_tvu = np.asarray(fit_par_tvu_strings).astype(np.float64)
                fit_tvu += fit_par_tvu  # adding two 3-element arrays

                fit_par_thu_strings = look_up_thu_data[31 * (w - 1) + k - 6].split(",")[:-1]  # exclude trailing \n
                fit_par_thu = np.asarray(fit_par_thu_strings).astype(np.float64)
                fit_thu += fit_par_thu  # adding two 3-element arrays

        fit_tvu /= len(self.kd_par)*len(self.wind_par)
        fit_thu /= len(self.kd_par)*len(self.wind_par)
        return fit_thu, fit_tvu

    def riegl_process(self, lut):
        """Retrieves the average fit for all kd given from reigl_look_up_fit.csv.
        reigl_look_up_fit.csv uses precalculated uncertainties based on riegl models.
        """

        look_up = open(lut)
        look_up_data = look_up.readlines()
        look_up.close()
        fit = np.asarray([0, 0, 0])
        for k in self.kd_par:
            fit_par_str = look_up_data[k-6].split(",")
            fit_par = np.asarray(fit_par_str)[:-1].astype(np.float64)
            fit += fit_par  # adding two 3-element arrays

        fit /= len(self.kd_par)

        return fit

    def get_subaqueous_meta_data(self):
        subaqueous_f = open(self.curr_lut, 'r')
        subaqueous_metadata = subaqueous_f.readline().split(',')
        subaqueous_f.close()
        subaqueous_metadata = {k: v.strip() for (k, v) in [n.split(':') for n in subaqueous_metadata]}
        return subaqueous_metadata


if __name__ == '__main__':
    pass

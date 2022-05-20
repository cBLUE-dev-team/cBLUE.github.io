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

WHY WERE THERE 0 COMMENTS IN THIS WHOLE FILE!?!?! (AAAAARGGGH!!!)

Last Edited:
Forrest Corcoran
3/30/2022
"""

# -*- coding: utf-8 -*-
# Oh, good. Thanks for the character encoding. That's what I really need to know...

import logging
import pandas as pd
import numpy as np
from os.path import join

logger = logging.getLogger(__name__)


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated
    """

    def __init__(self, surface, wind_par, kd_par, depth, sensor, subaqueous_luts):

        sensor_aliases = {
            "Riegl VQ-880-G": "RIEGL",
            "Leica Chiroptera 4X": "CHIRO",
            "Hawkeye 4X": "HAWK",
        }

        self.thu_path = join(".", "lookup_tables", "THU.csv")

        print("surface:", surface)
        self.surface = surface
        self.wind_par = wind_par
        self.kd_par = kd_par
        self.depth = depth
        self.sensor = sensor_aliases[sensor]  # get sensor alias as shown in config
        self.subaqueous_luts = subaqueous_luts
        self.curr_lut = None
        self.thu = None
        self.tvu = None

    def fit_lut(self):
        """Called to begin the SubAqueous processing."""

        if self.surface == 1:
            logger.subaqueous(f"using model {self.subaqueous_luts[self.sensor]}")

            self.curr_lut = self.subaqueous_luts[self.sensor]

            fit_tvu, fit_thu = self.riegl_process(self.curr_lut, self.thu_path)

        else:
            logger.subaqueous(f"using model {self.subaqueous_luts[self.sensor]}")
            self.curr_lut = self.subaqueous_luts["ECKV"]
            fit_tvu, fit_thu = self.model_process(self.curr_lut, self.thu_path)

        # horizontal uncertainty always quadratic (why? IDK... sorry)
        res_thu = fit_thu[0] * self.depth**2 + fit_thu[1] * self.depth + fit_thu[2]

        # if coeff length = 3, run quadratic model (ax2+bx+c)
        if len(fit_tvu) == 3:
            res_tvu = (
                fit_tvu[0] * self.depth**2 + fit_tvu[1] * self.depth + fit_tvu[2]
            )
            logger.subaqueous(f"subaqueous coeffs: \n tvu:{fit_tvu}, \n thu:{fit_thu}")

        # if coeff length = 2, run linear model (ax+b)
        elif len(fit_tvu) == 2:
            res_tvu = fit_tvu[0] * self.depth + fit_tvu[1]
            logger.subaqueous(f"subaqueous coeffs tvu:{fit_tvu}, thu:{fit_thu}")

        # otherwise, something is wrong
        else:
            logger.subaqueous(f"subaqueous coeffs tvu:{fit_tvu}, thu:{fit_thu}")
            raise ValueError(
                "Model generated wrong number of coefficients. 3 coeffs needed for quadratic model, 2 for linear. All other values are incorrect. Check log for details."
            )

        self.thu = res_thu.T
        self.tvu = res_tvu.T

        return self.thu, self.tvu

    def model_process(self, v_lut, h_lut):
        """Retrieves the average fit for all given combinations of wind and kd given from look_up_fit.csv.
        look_up_fit.csv uses precalculated uncertainties based on seasurface models.

        :param v_lut: The vertical Look Up Table used for modeling
        :param h_lut: The horizontal Look Up Table used for modeling
        :param wind: The wind values passed from the GUI
        :param kd: The turbidity values passed from the GUI

        :return: TVU and THU obs. equation coefficients
        :rtype: (ndarray, ndarray)
        """

        # values range from 0.06-0.32 (m^-1) so we need
        # the right indices from the table
        try:
            # (this is a potential pain point, wrapping in exception handler and logger)
            indices = [31 * (w - 1) + k - 6 for w in self.wind_par for k in self.kd_par]

            logger.subaqueous(f"Wind:{self.wind_par}, Kd:{self.kd_par}")

            # ensure integer indices
            if np.array(indices).dtype != int:
                raise Exception

        except Exception as e:
            logger.subaqueous(f"Wind:{self.wind_par}, Kd:{self.kd_par}")
            print(e)
            raise Exception(
                "Could not generate LUT indices for given wind, kd values. Check log for details"
            )

        # read tables, select rows, take column-wise mean
        fit_tvu = pd.read_csv(v_lut, names=None).iloc[indices].mean()
        fit_thu = pd.read_csv(h_lut, names=None).iloc[indices].mean()

        # metadata in the header - need to drop last column (all nans)
        return fit_tvu.to_numpy()[:-1], fit_thu.to_numpy()[:-1]

    def riegl_process(self, v_lut, h_lut):
        """Retrieves the average fit for all kd given from reigl_look_up_fit.csv.
        reigl_look_up_fit.csv uses precalculated uncertainties based on riegl models.

        :param v_lut: The vertical Look Up Table used for modeling
        :param h_lut: The horizontal Look Up Table used for modeling
        :param kd: The turbidity values passed from the GUI

        :return: TVU and THU obs. equation coefficients
        :rtype: (ndarray, ndarray)
        """

        # ensure numpy typing
        if type(self.kd_par) != np.ndarray:
            self.kd_par = np.array(self.kd_par)

        # read tables, select rows, take column-wise mean
        fit_tvu = pd.read_csv(v_lut).iloc[self.kd_par - 6].mean()
        fit_thu = pd.read_csv(h_lut, names=None).iloc[self.kd_par - 6].mean()

        # metadata in the header - need to drop last column (all nans)
        return fit_tvu.to_numpy(), fit_thu.to_numpy()[:-1]

    def get_subaqueous_meta_data(self):
        """I haven't the patience to figure out why we need the MC ray tracing
        metadata or if it's ever even used.
        """
        subaqueous_f = open(self.curr_lut, "r")
        subaqueous_metadata = subaqueous_f.readline().split(",")
        subaqueous_f.close()
        subaqueous_metadata = {
            k: v.strip() for (k, v) in [n.split(":") for n in subaqueous_metadata]
        }
        return subaqueous_metadata


# Why? When are you gonna use this by itself? This will never me a __main__
if __name__ == "__main__":
    pass

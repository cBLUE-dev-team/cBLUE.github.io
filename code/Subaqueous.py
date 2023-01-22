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

import logging
import pandas as pd
import numpy as np
from os.path import join

logger = logging.getLogger(__name__)


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated
    """

    def __init__(self, wind_par, kd_par, depth, sensor, subaqueous_luts):

        logging.subaqueous(f"sensor - {sensor} of type {type(sensor)}")
        sensor_aliases = {
            "Riegl VQ-880-G (0.7 mrad)": "RIEGL 0.7 mrad",
            "Riegl VQ-880-G (1.0 mrad)": "RIEGL 1.0 mrad",
            "Riegl VQ-880-G (1.5 mrad)": "RIEGL 1.5 mrad",
            "Riegl VQ-880-G (2.0 mrad)": "RIEGL 2.0 mrad",
            "Leica Chiroptera 4X (HawkEye 4X Shallow)": "CHIRO",
            "HawkEye 4X 400m AGL": "HAWK400",
            "HawkEye 4X 500m AGL": "HAWK500",
            "HawkEye 4X 600m AGL": "HAWK600",
        }

        self.wind_par = wind_par[1]
        self.kd_par = kd_par[1]
        self.depth = depth
        self.sensor = sensor_aliases[sensor]
        self.vert_lut = subaqueous_luts[self.sensor]["vertical"]
        self.horz_lut = subaqueous_luts[self.sensor]["horizontal"]

        logger.subaqueous(f"kd_par {self.kd_par}")
        logger.subaqueous(f"wind_par {self.wind_par}")
        logger.subaqueous(self.vert_lut)
        logger.subaqueous(self.horz_lut)

    def fit_lut(self):
        """Called to begin the SubAqueous processing."""

        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        fit_tvu, fit_thu = self.model_process(self.vert_lut, self.horz_lut)

        # a_h := horizontal linear coeffs
        # b_h := horizontal linear offsets
        # reshape to column vector
        a_h = fit_thu["a"].values.reshape(-1, 1)
        b_h = fit_thu["b"].values.reshape(-1, 1)

        # inner product of coeffs w/ depths + offsets
        # gives matrix of dims (#coeffs, #las points)
        res_thu = a_h @ self.depth.reshape(1, -1) + b_h

        # a_z := vertical linear coeffs
        # b_z := vertical linear offsets
        a_z = fit_tvu["a"].values.reshape(-1, 1)
        b_z = fit_tvu["b"].values.reshape(-1, 1)

        res_tvu = a_z @ self.depth.reshape(1, -1) + b_z

        # enforce minimum value for tvu
        res_tvu[res_tvu < min_tvu] = min_tvu

        # compute average over columns
        # (i.e. average over coeffs for each las point)
        self.thu = res_thu.mean(axis=0)
        self.tvu = res_tvu.mean(axis=0)

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

            # ensure integer indices
            if np.array(indices).dtype != int:
                raise Exception

        except Exception as e:
            print(e)
            raise Exception(
                "Could not generate LUT indices for given wind, kd values. Check log for details"
            )

        # read tables, select rows, take column-wise mean
        fit_tvu = pd.read_csv(v_lut, names=["a", "b"]).iloc[indices]
        fit_thu = pd.read_csv(h_lut, names=["a", "b"]).iloc[indices]

        # metadata in the header - need to drop last column (all nans)
        return fit_tvu, fit_thu

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

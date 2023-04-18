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

Last Edited:
Keana Kief (OSU)
April 12th, 2023
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated
    """

    def __init__(self, wind_par, kd_par, depth, sensor_object):

        self.wind_par = wind_par
        self.kd_par = kd_par
        self.depth = depth
        self.sensor_object = sensor_object

        logger.subaqueous(f"kd_par {self.kd_par}")
        logger.subaqueous(f"wind_par {self.wind_par}")
        logger.subaqueous(f"vertical lut {self.sensor_object.vert_lut}")
        logger.subaqueous(f"horizontal lut{self.sensor_object.horz_lut}")

    def fit_lut(self):
        """Called to begin the SubAqueous processing."""

        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        fit_tvu, fit_thu = self.model_process()

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

    def model_process(self):
        """Retrieves TVU and THU observation equation coefficients based on the linear regression of precalculated uncertainties
            from Monte Carlo simulations for all given permutations of wind and kd from the vertical and horizontal lookup
            tables for the sensor used. 

        :return: (fit_tvu, fit_thu) TVU and THU observation equation coefficients
        :rtype: (DataFrame, DataFrame)
        """
        # wind_par values range from 0-20 kts, represented as integers 1-10.
        # cBLUE gives users four options for Wind Speed:
        #   Wind Speed: Calm-light air (0-2 kts) == [1]
        #               Light Breeze (3-6 kts) == [2,3]
        #               Gentle Breeze (7-10 kts) == [4,5]
        #               Moderate Breeze (11-15 kts) == [6,7]
        #               Fresh Breeze (16-20 kts) == [8, 9, 10]

        # Turbidity (kd_par) values range from 0.06-0.36 (m^-1) and are represented as integers 6-36.
        # cBLUE gives users five options for Turbidity:
        #   kd: Clear (0.06-0.10 m^-1) == [6-10]
        #       Clear-Moderate (0.11-0.17 m^-1) == [11-17]
        #       Moderate (0.18-0.25 m^-1) == [18-25]
        #       Moderate-High (0.26-0.32 m^-1) == [26-32]
        #       High (0.33-0.36 m^-1) == [33-36]

        # self.wind_par and self.kd_par are used to get the right indices for the lookup table.
        # The lookup table rows are ordered by the permutations of wind speed (low to high) with turbidity (low to high).

        # ex: row 0 represents observation equation coefficients for wind speed 1 and kd 6, 
        #       row 1 represents wind speed 1 and kd 7, [...], row 278 represents wind speed 8 and kd 36, etc.  

        # For every permutation of values from the wind_par and kd_par arrays, get an index
        #  and add it to the indices array. 
        indices = [31 * (w - 1) + k - 6 for w in self.wind_par for k in self.kd_par]

        # Read tables, select rows
        fit_tvu = pd.read_csv(self.sensor_object.vert_lut, names=["a", "b"]).iloc[indices]
        fit_thu = pd.read_csv(self.sensor_object.horz_lut, names=["a", "b"]).iloc[indices]

        # Return TVU and THU observation equation coefficients DataFrames. 
        return fit_tvu, fit_thu

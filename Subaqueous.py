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
May 17th, 2024
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Subaqueous:
    """Processing of the SubAqueous portion of LIDAR TopoBathymetric TPU.
    To be used in conjunction with the associated
    """

    def __init__(self, gui_object, depth, sensor_object, classification):

        self.gui_object = gui_object
        self.depth = depth
        self.sensor_object = sensor_object
        self.classification = classification

        #A set of valid subaqeuous classification values:
        self.subaqueous_class_values  = gui_object.subaqueous_classes
        # print(type(self.subaqueous_class_values))
        # print(self.subaqueous_class_values)
        # self.subaqueous_class_values  = {40, 43, 46, 64}

        logger.subaqueous(f"kd_par {self.gui_object.kd_vals}")
        logger.subaqueous(f"wind_par {self.gui_object.wind_vals}")
        logger.subaqueous(f"vertical lut {self.sensor_object.vert_lut}")
        logger.subaqueous(f"horizontal lut{self.sensor_object.horz_lut}")

    def fit_lut(self):
        """Called to begin the SubAqueous processing."""
    
        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        fit_tvu, fit_thu = self.model_process()

        # Quadratic fit: a*depth^2 + b*depth + c
        # a_h := horizontal quadratic coefficient
        # b_h := horizontal linear coefficient
        # c_h := horizontal offset
        a_h = fit_thu["a"].to_numpy()
        b_h = fit_thu["b"].to_numpy()
        c_h = fit_thu["c"].to_numpy()

        # inner product of coeffs w/ depths + offsets
        # gives matrix of dims (#coeffs, #las points)
        res_thu = a_h @ np.square(self.depth.reshape(1,-1)) + b_h @ self.depth.reshape(1, -1) + c_h

        # Quadratic fit: a*depth^2 + b*depth + c
        # a_z := horizontal quadratic coefficient
        # b_z := horizontal linear coefficient
        # c_z := horizontal offset
        a_z = fit_tvu["a"].to_numpy()
        b_z = fit_tvu["b"].to_numpy()
        c_z = fit_tvu["c"].to_numpy()

        res_tvu = a_z @ np.square(self.depth.reshape(1,-1)) + b_z @ self.depth.reshape(1, -1) + c_z

        # enforce minimum value for tvu
        res_tvu[res_tvu < min_tvu] = min_tvu

        # Check classification values.
        for i, classification in enumerate(self.classification):
            # If the point is not subaqueous, set subaqueous THU and TVU values to 0.
            if classification not in self.gui_object.subaqueous_classes:
                print(f"Class: {classification}")
                res_thu[i] = 0
                res_tvu[i] = 0


        return res_thu, res_tvu

    def model_process(self):
        """Retrieves the averaged TVU and THU observation equation coefficients based on the linear regression of 
            precalculated uncertainties from Monte Carlo simulations for all given permutations of wind and kd. 

        :return: (mean_fit_tvu, mean_fit_thu) Averaged TVU and THU observation equation coefficients.
        :rtype: (DataFrame, DataFrame)
        """
        # wind_par values range from 0-20 kts, represented as integers 1-10.
        # cBLUE gives users five options for Wind Speed:
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

        # self.gui_object.wind_vals and self.gui_object.kd_vals are used to get the right indices for the lookup table.
        # The lookup table rows are ordered by the permutations of wind speed (low to high) with turbidity (low to high).

        # ex: row 0 represents observation equation coefficients for wind speed 1 and kd 6, 
        #       row 1 represents wind speed 1 and kd 7, [...], row 278 represents wind speed 8 and kd 36, etc.  

        # For every permutation of values from the wind_par and kd_par arrays, get an index
        #  and add it to the indices array. 
        indices = [31 * (w - 1) + k - 6 for w in self.gui_object.wind_vals for k in self.gui_object.kd_vals]

        #Get columns a, b and c if they exist
        #Linear fits: bx + c
        #Quadratic fits: ax^2 + bx + c
        cols = ['a', 'b', 'c']
        # Read look up tables, select rows
        fit_tvu = pd.read_csv(self.sensor_object.vert_lut, usecols=lambda i: i in set(cols)).iloc[indices]
        fit_thu = pd.read_csv(self.sensor_object.horz_lut, usecols=lambda i: i in set(cols)).iloc[indices]

        #If this is a linear fit with no a coefficient 
        if 'a' not in fit_thu:
            #Take mean result for each column of the indicies returned
            mean_fit_tvu = pd.DataFrame([fit_tvu.mean(axis=0)], columns=["b","c"])
            mean_fit_thu = pd.DataFrame([fit_thu.mean(axis=0)], columns=["b","c"])

            #Add a c column and set it to 0
            mean_fit_tvu['a'] = 0 
            mean_fit_thu['a'] = 0
        else:
            #Take mean result for each column of the indicies returned
            mean_fit_tvu = pd.DataFrame([fit_tvu.mean(axis=0)], columns=["a","b","c"])
            mean_fit_thu = pd.DataFrame([fit_thu.mean(axis=0)], columns=["a","b","c"])

        # Return averaged TVU and THU observation equation coefficient DataFrames. 
        return mean_fit_tvu, mean_fit_thu
    
    def multi_beam_fit_lut(self, masked_fan_angle):
        """Called to begin the SubAqueous processing for multi beam sensors"""
    
        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        fit_tvu, fit_thu = self.multi_beam_model_process()

        # a_h := horizontal linear coeffs
        # b_h := horizontal linear offsets
        a_h = fit_thu["a"].to_numpy()
        b_h = fit_thu["b"].to_numpy()

        # a_z := vertical linear coeffs
        # b_z := vertical linear offsets
        a_z = fit_tvu["a"].to_numpy()
        b_z = fit_tvu["b"].to_numpy()

        # logger.subaqueous(f"Horizontal coefficents: {a_h}")
        # logger.subaqueous(f"Horizontal offsets: {b_h}")
        # logger.subaqueous(f"Vertical coefficents: {a_z}")
        # logger.subaqueous(f"Vertical offsets: {b_z}")

        res_thu = []
        res_tvu = []
        #Index for checking classification values
        i = 0

        #Loop through the depth and the masked fan angle
        for depth_point, fan_angle_point in zip(self.depth, masked_fan_angle):
            
            # Check classification values.
            # If the point is not subaqueous, set subaqueous THU and TVU values to 0.
            if self.classification[i] not in self.gui_object.subaqueous_classes:
                # print(f'Not Subaqueous Class: {self.classification[i]}')
                res_tvu.append(0)
                res_thu.append(0)

            # If the point is subaqueous, calculate THU and TVU values. 
            else:
     
                # print(f'Subaqueous Class: {self.classification[i]}')
                # Use the fan angle at this point an an index to get the
                #  horizontal coefficent and offset for this depth point
                a_h_point = a_h[fan_angle_point]
                b_h_point = b_h[fan_angle_point]

                # Product of coeffs w/ depths + offsets
                thu_point = a_h_point * depth_point + b_h_point

                #Add the subaqueous thu at this point to the list of result thu values
                res_thu.append(thu_point)

                #Use the fan angle at this point an an index to get the
                #  vertical coefficent and offset for this depth point
                a_z_point = a_z[fan_angle_point]
                b_z_point = b_z[fan_angle_point]

                # Product of coeffs w/ depths + offsets
                tvu_point = a_z_point * depth_point + b_z_point

                # enforce minimum value for tvu
                if(tvu_point < min_tvu):
                    tvu_point = min_tvu

                #Add the subaqueous tvu at this point to the list of result thu values
                res_tvu.append(tvu_point)
            
            # Increment counter for checking classification values.
            i += 1

        return np.asarray(res_thu), np.asarray(res_tvu)
    
    def multi_beam_model_process(self):
        """Retrieves the page of TVU and THU observation equation coefficients for all fan angles for the given combination
            of wind and kd. TVU and THU observation equation coefficients are based on the linear regression of 
            precalculated uncertainties from Monte Carlo simulations  

        :return: (fit_tvu, fit_thu) TVU and THU observation equation coefficients for each fan angle.
        :rtype: (DataFrame, DataFrame)
        """

        # kd_ind are index values that range from 0-4 and represent the user's selection for Turbidity.
        # cBLUE gives users five options for Turbidity:
        #   kd: 0: ("Clear (0.06-0.10 m^-1)", range(6, 11)),
        #       1: ("Clear-Moderate (0.11-0.17 m^-1)", range(11, 18)),
        #       2: ("Moderate (0.18-0.25 m^-1)", range(18, 26)),
        #       3: ("Moderate-High (0.26-0.32 m^-1)", range(26, 33)),
        #       4: ("High (0.33-0.36 m^-1)", range(33, 37))

        # wind_ind are index values that range from 0-4 and represent the user's selection for wind speed.
        # cBLUE gives users five options for Wind Speed:
        #   Wind Speed: 0: ("Calm-light air (0-2 kts)", [1]),
        #               1: ("Light Breeze (3-6 kts)", [2, 3]),
        #               2: ("Gentle Breeze (7-10 kts)", [4, 5]),
        #               3: ("Moderate Breeze (11-15 kts)", [6, 7]),
        #               4: ("Fresh Breeze (16-20 kts)", [8, 9, 10])

        # self.gui_object.wind_ind and self.gui_object.kd_ind are used to get the right sheet from the lookup table.
        # The excel sheets are ordered by the permutations of turbidity (low to high) with wind speed (low to high).

        # ex: sheet 0 represents fan angle observation equation coefficients for kd selection 0 and wind speed selection 0, 
        #       sheet 1 represents kd selection 0 and wind speed selection 1, [...],
        #       sheet 24 represents kd selection 4 and wind speed selection 4, etc.  

        # Get the sheet number for this combination of wind_ind and kd_ind. 
        sheet = (5 * self.gui_object.kd_ind) + self.gui_object.wind_ind

        logger.subaqueous(f"kd_ind: {self.gui_object.kd_ind}, wind_ind: {self.gui_object.wind_ind}")
        logger.subaqueous(f"Multi beam look up table sheet number: {sheet}")

        # Read look up tables, select rows
        fit_tvu = pd.read_excel(self.sensor_object.vert_lut, sheet_name=sheet, header=None, names=["a", "b"])
        fit_thu = pd.read_excel(self.sensor_object.horz_lut, sheet_name=sheet, header=None, names=["a", "b"])

        # logger.subaqueous(f"Multi beam fit_tvu: {fit_tvu}")
        # logger.subaqueous(f"Multi beam fit_thu: {fit_thu}")

        # Return DataFrames of TVU and THU observation equation coefficients for each fan angle. 
        return fit_tvu, fit_thu

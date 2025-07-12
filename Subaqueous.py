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
July 9th, 2025
"""

import logging
import pandas as pd
import numpy as np
from math import sqrt

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

        logger.subaqueous(f"kd_par {self.gui_object.kd_ind}")
        logger.subaqueous(f"wind_par {self.gui_object.wind_ind}")
        logger.subaqueous(f"vertical lut {self.sensor_object.vert_lut}")
        logger.subaqueous(f"horizontal lut{self.sensor_object.horz_lut}")

    def fit_lut(self):
        """Called to begin the SubAqueous processing."""
    
        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        fit_tvu, fit_thu, range_bias = self.model_process()

        # Range Bias Uncertainty is a 3rd order polynomial fit: ax^3 + bx^2 + cx + d
        a_rb = range_bias["a"].to_numpy()
        b_rb = range_bias["b"].to_numpy()
        c_rb = range_bias["c"].to_numpy()
        d_rb = range_bias["d"].to_numpy()

        res_range_bias = res_tvu = a_rb @ np.power(self.depth.reshape(1,-1), 3) + b_rb @ np.square(self.depth.reshape(1, -1)) + c_rb @ self.depth.reshape(1, -1) + d_rb

        # a_z := vertical a coefficient
        # b_z := vertical b coefficient
        a_z = fit_tvu["a"].to_numpy()
        b_z = fit_tvu["b"].to_numpy()
        # TVU is a polynomial fit: (a^2+(b*x)^2)^0.5
        res_tvu =  np.sqrt(np.square(a_z) + np.square(b_z @ self.depth.reshape(1,-1)))

        # enforce minimum value for tvu
        res_tvu[res_tvu < min_tvu] = min_tvu

        # a_h := horizontal coefficient
        # b_h := horizontal offset
        a_h = fit_thu["a"].to_numpy()
        b_h = fit_thu["b"].to_numpy()
        # THU is a Linear fit: a + b*x 
        res_thu = a_h + b_h @ self.depth.reshape(1, -1)

        # Check classification values.
        for i, classification in enumerate(self.classification):
            # If the point is not subaqueous, set range bias and subaqueous THU and TVU values to 0.
            if classification not in self.gui_object.subaqueous_classes:
                res_thu[i] = 0
                res_tvu[i] = 0
                res_range_bias[i] = 0
            # else:
            #     print(f"subaqueous tvu[{i}]: {res_tvu[i]}")


        return res_tvu, res_thu, res_range_bias

    def model_process(self):
        """Retrieves the TVU, THU, and range uncertainty observation equation coefficients and offsets based 
            on the polynomial regression of precalculated uncertainties from Monte Carlo simulations for all 
            given permutations of wind and kd. 

        :return: (tvu, thu, range_bias) TVU, THU, and range bias observation equation coefficients.
        :rtype: (DataFrame, DataFrame, DataFrame)
        """
        # wind_par values range from 0-20 kts, represented as integers 0-4.
        # cBLUE gives users five options for Wind Speed:
        #   Wind Speed: "Calm-light air [0-4] kts" == 0,
        #               "Light Breeze (4-8] kts" == 1,
        #               "Gentle Breeze (8-12] kts" == 2,
        #               "Moderate Breeze (12-16] kts" == 3,
        #               "Fresh Breeze (16-20+] kts == 4"

        # Turbidity (kd_par) values range from 0.11-0.58 (m^-1) and are represented as integers 0-5.
        # This represents six Jerlov types: III = 0.11 , IC = 0.13, 3C = 0.17, 
        #                                   5C = 0.24, 7C = 0.35, 9C = 0.58

        # cBLUE gives users six options for Turbidity:
        #   kd: Clear [0-0.12] m^-1 == 0,
        #       Clear-Moderate (0.12-0.15] m^-1 == 1,
        #       Moderate (0.15-0.21] m^-1 == 2,
        #       Moderate-Turbid (0.21-0.27] m^-1 == 3,
        #       Turbid (0.27-0.47] m^-1) == 4,
        #       Very Turbid (0.47-0.58+] m^-1 == 5
        
        # self.gui_object.wind_ind and self.gui_object.kd_ind are used to get the right indices for the lookup table.

        # The lookup table rows are ordered by the permutations of wind speed (low to high) with turbidity (low to high).
        # ex: row 0 represents observation equation coefficients for wind speed index 0 "Calm-light air" and kd index 0 "Clear", 
        #     row 1 represents wind speed index 0 "Calm-light air" and kd index 1 "Clear-Moderate", 
        #     [...], row 29 represents wind speed index 4 "Fresh Breeze" and kd index 5 "Very Turbid".

        index = 5*self.gui_object.wind_ind + 1*self.gui_object.wind_ind + self.gui_object.kd_ind

        # Columns to grab from the LUTs. 
        # Get columns a, b from vert and horz LUTs. 
        # Get columns a, b, c, d from range bias LUT. 
        cols = ['a', 'b', 'c', 'd']
        # Read look up tables, select rows
        # The lambda statement will only grab columns that exist in the csv file. That way we can get columns a and b
        # from the vertical and horizontal LUTs, and columns a, b, c, and d from the range bias LUT. 

        tvu = pd.read_csv(self.sensor_object.vert_lut, usecols=lambda i: i in set(cols)).iloc[index]
        thu = pd.read_csv(self.sensor_object.horz_lut, usecols=lambda i: i in set(cols)).iloc[index]
        range_bias = pd.read_csv(self.sensor_object.range_bias_lut, usecols=lambda i: i in set(cols)).iloc[index]

        # print(f"TVU Deep Narrow: {tvu_deep_narrow} and THU Deep Narrow: {thu_deep_narrow}")
        # print(f"TVU Deep Wide: {tvu_deep_wide} and THU Deep Wide: {thu_deep_wide}")
        # print(f"TVU Shallow: {tvu_shallow} and THU Shallow: {thu_shallow}")
        # print(f"Range Bias Uncertainty: {range_bias}")

        # Return averaged TVU and THU observation equation coefficient DataFrames. 
        return tvu, thu, range_bias
    
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

        #Loop through the depth and the masked fan angle
        for depth_point, fan_angle_point, class_point in zip(self.depth, masked_fan_angle, self.classification):
            
            # Check classification values.
            # If the point is not subaqueous, set subaqueous THU and TVU values to 0.
            if class_point not in self.gui_object.subaqueous_classes:
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

        return np.asarray(res_tvu), np.asarray(res_thu)
    
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

        wind_ind = self.gui_object.wind_ind
        # To account for new selection options
        if wind_ind == 5:
            wind_ind = 4  

        # Get the sheet number for this combination of wind_ind and kd_ind. 
        sheet = (5 * self.gui_object.kd_ind) + wind_ind

        logger.subaqueous(f"kd_ind: {self.gui_object.kd_ind}, wind_ind: {self.gui_object.wind_ind}")
        logger.subaqueous(f"Multi beam look up table sheet number: {sheet}")

        # Read look up tables, select rows
        fit_tvu = pd.read_excel(self.sensor_object.vert_lut, sheet_name=sheet, header=None, names=["a", "b"])
        fit_thu = pd.read_excel(self.sensor_object.horz_lut, sheet_name=sheet, header=None, names=["a", "b"])

        # logger.subaqueous(f"Multi beam fit_tvu: {fit_tvu}")
        # logger.subaqueous(f"Multi beam fit_thu: {fit_thu}")

        # Return DataFrames of TVU and THU observation equation coefficients for each fan angle. 
        return fit_tvu, fit_thu

    
    def hawkeye_fit_lut(self, masked_hawkeye_data):
        """Called to begin the SubAqueous processing."""
    
        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        tvu_deep_narrow, thu_deep_narrow, tvu_deep_wide, thu_deep_wide, tvu_shallow, thu_shallow, range_bias = self.hawkeye_model_process()

        # TVU is a polynomial fit: (a^2+(b*x)^2)^0.5
        # a_z := vertical a coefficient
        # b_z := vertical b coefficient

        a_z_narrow = tvu_deep_narrow["a"].to_numpy()
        b_z_narrow = tvu_deep_narrow["b"].to_numpy()

        a_z_wide = tvu_deep_wide["a"].to_numpy()
        b_z_wide = tvu_deep_wide["b"].to_numpy()                                                                 

        a_z_shallow = tvu_shallow["a"].to_numpy()
        b_z_shallow = tvu_shallow["b"].to_numpy()

        # THU is a Linear fit: b + a*x 
        # a_h := horizontal coefficient
        # b_h := horizontal offset
        a_h_narrow = thu_deep_narrow["a"].to_numpy()
        b_h_narrow = thu_deep_narrow["b"].to_numpy()

        a_h_wide = thu_deep_wide["a"].to_numpy()
        b_h_wide = thu_deep_wide["b"].to_numpy()

        a_h_shallow = thu_shallow["a"].to_numpy()
        b_h_shallow = thu_shallow["b"].to_numpy()

        # Range Bias Uncertainty is a 3rd order polynomial fit: ax^3 + bx^2 + cx + d
        a_rb = range_bias["a"].to_numpy()
        b_rb = range_bias["b"].to_numpy()
        c_rb = range_bias["c"].to_numpy()
        d_rb = range_bias["d"].to_numpy()

        res_range_bias = res_tvu = a_rb @ np.power(self.depth.reshape(1,-1), 3) + b_rb @ np.square(self.depth.reshape(1, -1)) + c_rb @ self.depth.reshape(1, -1) + d_rb

        res_thu = []
        res_tvu = []
        
        # Product of coeffs w/ depths + offsets.
        # Loop through the depth, scanner channel, and user data
        for i, (depth_point, hawkeye_data_array, class_point) in enumerate(zip(self.depth, masked_hawkeye_data, self.classification)):

            
            # Check classification values.
            # If the point is not subaqueous, set range bias and subaqueous THU and TVU values to 0.
            if class_point not in self.gui_object.subaqueous_classes:
                # print(f'Not Subaqueous Class: {self.classification[i]}')
                thu_point = 0
                tvu_point = 0
                res_range_bias[i] = 0

            # Topographic scanner, only one channel exists
            # Scanner Channel: 1, User data: 0

            # Shallow scanner, only one channel exists 
            # Scanner channel: 2, User data: 0

            # Deep scanner, narrow channel
            # Scanner channel: 3, User data: 0

            # Deep scanner, combined channel (wide)
            # Scanner channel: 3, User data: 1

            # hawkeye_data_array[0] = masked scanner_channel, 
            # hawkeye_data_array[1] = masked user_data
            
            # If Scanner Channel = 1, then this is topographic scanner data. 
            # There is no subaqueous uncertainty.
            elif(hawkeye_data_array[0] == 1):
                thu_point = 0
                tvu_point = 0
            # If Scanner Channel = 2 and User Data = 0, then this is the shallow scanner
            # Use the shallow uncertainty coefficients and offset. 
            elif(hawkeye_data_array[0] == 2 and hawkeye_data_array[1] == 0):
                # THU is a Linear fit: a + b*x 
                thu_point = a_h_shallow + (b_h_shallow * depth_point) 
                # TVU is a polynomial fit: (a^2+(b*x)^2)^0.5
                bx_h_shallow = (b_z_shallow * depth_point)
                tvu_point = sqrt((a_z_shallow*a_z_shallow) + (bx_h_shallow*bx_h_shallow))
                # enforce minimum value for tvu
                if(tvu_point < min_tvu):
                    tvu_point = min_tvu
            # If Scanner Channel = 3 and User Data = 1, then this is the deep scanner, combined channel
            # Use the deep wide uncertainty coefficients and offset. 
            elif(hawkeye_data_array[0] == 3 and hawkeye_data_array[1] == 1):
                # THU is a Linear fit: a + b*x 
                thu_point = a_h_wide + (b_h_wide * depth_point) 
                # TVU is a polynomial fit: (a^2+(b*x)^2)^0.5
                bx_h_wide = (b_z_wide * depth_point)
                tvu_point = sqrt((a_z_wide*a_z_wide) + (bx_h_wide*bx_h_wide))
                # enforce minimum value for tvu
                if(tvu_point < min_tvu):
                    tvu_point = min_tvu
            # If Scanner Channel = 3 and User Data = 0, then this is the deep scanner, narrow channel
            # Use the deep narrow uncertainty coefficients and offset. 
            else:   
                # THU is a Linear fit: a + b*x 
                thu_point = a_h_narrow + (b_h_narrow * depth_point) 
                # TVU is a polynomial fit: (a^2+(b*x)^2)^0.5
                bx_h_narrow = (b_z_narrow * depth_point)
                tvu_point = sqrt((a_z_narrow*a_z_narrow) + (bx_h_narrow*bx_h_narrow))
                # enforce minimum value for tvu
                if(tvu_point < min_tvu):
                    tvu_point = min_tvu

            #Add the subaqueous thu at this point to the list of result thu values
            res_thu.append(thu_point)
            #Add the subaqueous tvu at this point to the list of result thu values
            res_tvu.append(tvu_point)


        return np.asarray(res_tvu), np.asarray(res_thu), np.asarray(res_range_bias)

    def hawkeye_model_process(self):
        """Retrieves the TVU, THU, and range uncertainty observation equation coefficients and offsets based 
            on the polynomial regression of precalculated uncertainties from Monte Carlo simulations for all 
            given permutations of wind and kd. 

        :return: (tvu_deep_narrow, thu_deep_narrow, tvu_deep_wide, thu_deep_wide, tvu_shallow, thu_shallow, range_bias ) TVU, THU, and range bias observation equation coefficients.
        :rtype: (DataFrame, DataFrame, DataFrame, DataFrame, DataFrame, DataFrame, DataFrame)
        """
        # wind_par values range from 0-20 kts, represented as integers 0-4.
        # cBLUE gives users five options for Wind Speed:
        #   Wind Speed: "Calm-light air [0-4] kts" == 0,
        #               "Light Breeze (4-8] kts" == 1,
        #               "Gentle Breeze (8-12] kts" == 2,
        #               "Moderate Breeze (12-16] kts" == 3,
        #               "Fresh Breeze (16-20+] kts == 4"

        # Turbidity (kd_par) values range from 0.11-0.58 (m^-1) and are represented as integers 0-5.
        # This represents six Jerlov types: III = 0.11 , IC = 0.13, 3C = 0.17, 
        #                                   5C = 0.24, 7C = 0.35, 9C = 0.58

        # cBLUE gives users six options for Turbidity:
        #   kd: Clear [0-0.12] m^-1 == 0,
        #       Clear-Moderate (0.12-0.15] m^-1 == 1,
        #       Moderate (0.15-0.21] m^-1 == 2,
        #       Moderate-Turbid (0.21-0.27] m^-1 == 3,
        #       Turbid (0.27-0.47] m^-1) == 4,
        #       Very Turbid (0.47-0.58+] m^-1 == 5

        # self.gui_object.wind_ind and self.gui_object.kd_ind are used to get the right indices for the lookup table.
        # The lookup table rows are ordered by the permutations of wind speed (low to high) with turbidity (low to high).
        # ex: row 0 represents observation equation coefficients for wind speed index 0 "Calm-light air" and kd index 0 "Clear", 
        #     row 1 represents wind speed index 0 "Calm-light air" and kd index 1 "Clear-Moderate", 
        #     [...], row 29 represents wind speed index 4 "Fresh Breeze" and kd index 5 "Very Turbid".

        index = 5*self.gui_object.wind_ind + 1*self.gui_object.wind_ind + self.gui_object.kd_ind

        # Columns to grab from the LUTs. 
        # Get columns a, b from vert and horz LUTs. 
        # Get columns a, b, c, d from range bias LUT. 
        cols = ['a', 'b', 'c', 'd']
        # Read look up tables, select rows
        # The lambda statement will only grab columns that exist in the csv file. That way we can get columns a and b
        # from the vertical and horizontal LUTs, and columns a, b, c, and d from the range bias LUT. 
        tvu_deep_narrow = pd.read_csv(self.sensor_object.vert_lut_deep_narrow, usecols=lambda i: i in set(cols)).iloc[index]
        thu_deep_narrow = pd.read_csv(self.sensor_object.horz_lut_deep_narrow, usecols=lambda i: i in set(cols)).iloc[index]
        tvu_deep_wide = pd.read_csv(self.sensor_object.vert_lut_deep_wide, usecols=lambda i: i in set(cols)).iloc[index]
        thu_deep_wide = pd.read_csv(self.sensor_object.horz_lut_deep_wide, usecols=lambda i: i in set(cols)).iloc[index]
        tvu_shallow = pd.read_csv(self.sensor_object.vert_lut_shallow, usecols=lambda i: i in set(cols)).iloc[index]
        thu_shallow = pd.read_csv(self.sensor_object.horz_lut_shallow, usecols=lambda i: i in set(cols)).iloc[index]
        range_bias = pd.read_csv(self.sensor_object.range_bias_lut, usecols=lambda i: i in set(cols)).iloc[index]

        # print(f"TVU Deep Narrow: {tvu_deep_narrow} and THU Deep Narrow: {thu_deep_narrow}")
        # print(f"TVU Deep Wide: {tvu_deep_wide} and THU Deep Wide: {thu_deep_wide}")
        # print(f"TVU Shallow: {tvu_shallow} and THU Shallow: {thu_shallow}")
        # print(f"Range Bias Uncertainty: {range_bias}")

        # Return averaged TVU and THU observation equation coefficient DataFrames. 
        return tvu_deep_narrow, thu_deep_narrow, tvu_deep_wide, thu_deep_wide, tvu_shallow, thu_shallow, range_bias
    
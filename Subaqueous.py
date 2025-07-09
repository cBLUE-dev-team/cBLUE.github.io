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
        self.subaqueous_class_values  = {40, 43, 46, 64}

        logger.subaqueous(f"kd_par {self.gui_object.kd_ind}")
        logger.subaqueous(f"wind_par {self.gui_object.wind_ind}")
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
            if classification not in self.subaqueous_class_values:
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

        # self.gui_object.wind_ind and self.gui_object.kd_ind are used to get the right indices for the lookup table.
        # The lookup table rows are ordered by the permutations of wind speed (low to high) with turbidity (low to high).

        # ex: row 0 represents observation equation coefficients for wind speed 1 and kd 6, 
        #       row 1 represents wind speed 1 and kd 7, [...], row 278 represents wind speed 8 and kd 36, etc.  

        # For every permutation of values from the wind_par and kd_par arrays, get an index
        #  and add it to the indices array. 
        indices = [31 * (w - 1) + k - 6 for w in self.gui_object.wind_ind for k in self.gui_object.kd_ind]

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

            #Add an "a" column and set it to 0
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
            if self.classification[i] not in self.subaqueous_class_values:
                # logger.subaqueous(f'Not Subaqueous Class: {self.classification[i]}')
                res_tvu.append(0)
                res_thu.append(0)

            # If the point is subaqueous, calculate THU and TVU values. 
            else:
     
                # logger.subaqueous(f'Subaqueous Class: {self.classification[i]}')
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
    
    def hawkeye_fit_lut(self, masked_leica_data):
        """Called to begin the SubAqueous processing."""
    
        # tvu values below 0.03 are considered erroneous
        min_tvu = 0.03

        # query coefficients from look up tables
        fit_tvu_narrow, fit_thu_narrow, fit_tvu_wide, fit_thu_wide = self.hawkeye_model_process()

        # Quadratic fit: a*depth^2 + b*depth + c
        # a_h := horizontal quadratic coefficient
        # b_h := horizontal linear coefficient
        # c_h := horizontal offset
        a_h_narrow = fit_thu_narrow["a"].to_numpy()
        b_h_narrow = fit_thu_narrow["b"].to_numpy()
        c_h_narrow = fit_thu_narrow["c"].to_numpy()
        
        a_h_wide = fit_thu_wide["a"].to_numpy()
        b_h_wide = fit_thu_wide["b"].to_numpy()
        c_h_wide = fit_thu_wide["c"].to_numpy()

        # a_z := horizontal quadratic coefficient
        # b_z := horizontal linear coefficient
        # c_z := horizontal offset
        a_z_narrow = fit_tvu_narrow["a"].to_numpy()
        b_z_narrow = fit_tvu_narrow["b"].to_numpy()
        c_z_narrow = fit_tvu_narrow["c"].to_numpy()

        a_z_wide = fit_tvu_wide["a"].to_numpy()
        b_z_wide = fit_tvu_wide["b"].to_numpy()                                                                 
        c_z_wide = fit_tvu_wide["c"].to_numpy()

        res_thu = []
        res_tvu = []

        # Product of coeffs w/ depths + offsets.
        # Loop through the depth, scanner channel, and user data
        for depth_point, leica_data_array in zip(self.depth, masked_leica_data):
            
            # leica_data_array[0] = masked scanner_channel, 
            # leica_data_array[1] = masked user_data

            # If Scanner Channel = 1, then this is topographic scanner data. 
            # There is no subaqueous uncertainty.
            if(leica_data_array[0] == 1):
                thu_point = 0
                tvu_point = 0
            # If Scanner Channel = 3 and User Data = 1, then this is the deep scanner, combined channel
            # Use the wide uncertainty coefficients and offset. 
            elif(leica_data_array[0] == 3 and leica_data_array[1] == 1):
                thu_point = (a_h_wide * np.square(depth_point)) + (b_h_wide * depth_point) + c_h_wide
                tvu_point = (a_z_wide * np.square(depth_point)) + (b_z_wide * depth_point) + c_z_wide
                # enforce minimum value for tvu
                if(tvu_point < min_tvu):
                    tvu_point = min_tvu
            # If Scanner Channel = 2 and User Data = 0, then this is the shallow scanner
            # If Scanner Channel = 3 and User Data = 0, then this is the deep scanner, narrow channel
            # Either way, use the narrow uncertainty coefficients and offset. 
            else:   
                thu_point = (a_h_narrow * np.square(depth_point)) + (b_h_narrow * depth_point) + c_h_narrow
                tvu_point = (a_z_narrow * np.square(depth_point)) + (b_z_narrow * depth_point) + c_z_narrow
                # enforce minimum value for tvu
                if(tvu_point < min_tvu):
                    tvu_point = min_tvu

            #Add the subaqueous thu at this point to the list of result thu values
            res_thu.append(thu_point)
            #Add the subaqueous tvu at this point to the list of result thu values
            res_tvu.append(tvu_point)           

        return np.asarray(res_thu), np.asarray(res_tvu)

    def hawkeye_model_process(self):
        """Retrieves the TVU and THU observation equation coefficients and offsets based on the polynomial regression of 
            precalculated uncertainties from Monte Carlo simulations for all given permutations of wind and kd. 

        :return: (tvu_narrow, thu_narrow, tvu_wide, thu_wide) TVU and THU observation equation coefficients.
        :rtype: (DataFrame, DataFrame)
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
        tvu_deep_narrow = pd.read_csv(self.sensor_object.vert_lut_narrow, usecols=lambda i: i in set(cols)).iloc[index]
        thu_deep_narrow = pd.read_csv(self.sensor_object.horz_lut_narrow, usecols=lambda i: i in set(cols)).iloc[index]
        tvu_deep_wide = pd.read_csv(self.sensor_object.vert_lut_wide, usecols=lambda i: i in set(cols)).iloc[index]
        thu_deep_wide = pd.read_csv(self.sensor_object.horz_lut_wide, usecols=lambda i: i in set(cols)).iloc[index]
        tvu_shallow = pd.read_csv(self.sensor_object.vert_lut_wide, usecols=lambda i: i in set(cols)).iloc[index]
        thu_shallow = pd.read_csv(self.sensor_object.horz_lut_wide, usecols=lambda i: i in set(cols)).iloc[index]
        range_bias = pd.read_csv(self.sensor_object.range_bias_lut, usecols=lambda i: i in set(cols)).iloc[index]

        # print(f"TVU Deep Narrow: {tvu_deep_narrow} and THU Deep Narrow: {thu_deep_narrow}")
        # print(f"TVU Deep Wide: {tvu_deep_wide} and THU Deep Wide: {thu_deep_wide}")
        # print(f"TVU Shallow: {tvu_shallow} and THU Shallow: {thu_shallow}")
        # print(f"Range Bias Uncertainty: {range_bias}")

        # Return averaged TVU and THU observation equation coefficient DataFrames. 
        return tvu_deep_narrow, thu_deep_narrow, tvu_deep_wide, thu_deep_wide, tvu_shallow, thu_shallow, range_bias
    
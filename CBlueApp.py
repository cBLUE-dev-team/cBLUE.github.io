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

Last Edited By:
Austin Anderson (NV5 Geospatial) and Keana Kief (OSU)
September 25th, 2023

"""

# -*- coding: utf-8 -*-
import logging
import sys
# Customize logging
import utils
import os
import json
import laspy
from Subaerial import SensorModel, Jacobian
from Merge import Merge
from Sbet import Sbet
from Tpu import Tpu
from Sensor import Sensor
from UserInput import UserInput
import argparse
from datetime import datetime
import subprocess

#Create a logging file named CBlue.log stored in the current working directory
utils.CustomLogger(filename="CBlue.log")

WIND_OPTIONS = [
        "Calm-light air (0-2 kts)",
        "Light Breeze (3-6 kts)",
        "Gentle Breeze (7-10 kts)",
        "Moderate Breeze (11-15 kts)",
        "Fresh Breeze (16-20 kts)"
    ]

TURBIDITY_OPTIONS = [
        "Clear (0.06-0.10 m^-1)",
        "Clear-Moderate (0.11-0.17 m^-1)",
        "Moderate (0.18-0.25 m^-1)",
        "Moderate-High (0.26-0.32 m^-1)",
        "High (0.33-0.36 m^-1)"
    ]

TPU_METRIC_OPTIONS = ["1-\u03c3", "95% confidence"]


def CBlueApp(controller_configuration):
    """Run CBLUE main process. Trajectory Processing will be followed by TPU Processing without interruption"""

    with open("cBLUE_ASCII_splash.txt", "r") as f:
        message = f.read()
        print(message)
    sbet_dir_value = controller_configuration["directories"]["sbet"]
    selected_sensor_value = controller_configuration["sensor_model"]
    sbet = Sbet(sbet_dir_value, selected_sensor_value)
    sbet.set_data()
    las_dir_value = controller_configuration["directories"]["las"]
    sensor_model = SensorModel(selected_sensor_value)
    settings_object = UserInput(controller_configuration)

    # Create a sensor object initialized to the user's selected sensor
    sensor_object = Sensor(selected_sensor_value)

    # Initialize the tpu object
    tpu = Tpu(settings_object, sensor_object)

    las_files = [
        os.path.join(las_dir_value, l)
        for l in os.listdir(las_dir_value)
        if l.endswith(".las") | l.endswith(".laz")
    ]
    num_las = len(las_files)

    # GENERATE JACOBIAN FOR SENSOR MODEL OBSERVATION EQUATIONS
    jacobian = Jacobian(sensor_model)

    # CREATE OBJECT THAT PROVIDES FUNCTIONALITY TO MERGE LAS AND TRAJECTORY DATA
    merge = Merge(sensor_object)
    logging.cblue(f"processing {num_las} las file(s) ({settings_object.cpu_process_info[0]})...")
    logging.cblue(f"multiprocessing = {settings_object.multiprocess}")

    def sbet_las_tiles_generator():
        """This generator is the 2nd argument for the run_tpu_multiprocessing method,
        to avoid passing entire sbet or list of tiled sbets to the calc_tpu() method"""
        for las_file in las_files:
            sbet_tile = os.path.split(las_file)[-1]
            logging.cblue(f"({sbet_tile}) generating SBET tile...")
            inFile = laspy.read(las_file)
            west = inFile.header.x_min
            east = inFile.header.x_max
            north = inFile.header.y_max
            south = inFile.header.y_min
            yield sbet.get_tile_data(north, south, east, west), las_file, jacobian, merge

    if settings_object.multiprocess == "True":
        p = tpu.run_tpu_multiprocess(num_las, sbet_las_tiles_generator())
        p.close()
        p.join()
    elif settings_object.multiprocess == "False":
        tpu.run_tpu_singleprocess(num_las, sbet_las_tiles_generator())
    else:
        logging.cblue(f"multiprocessing set to {settings_object.multiprocess} (Must be True or False)")
    print("Done!")

def updateConfig(config_dict):
    """Updates the cblue_configuration.json with the current run's settings."""
    new_config_dict = config_dict.copy()
    del new_config_dict["wind_ind"]
    del new_config_dict["wind_selection"]
    del new_config_dict["wind_vals"]
    del new_config_dict["kd_ind"]
    del new_config_dict["kd_selection"]
    del new_config_dict["kd_vals"]
    del new_config_dict["vdatum_region"]
    del new_config_dict["mcu"]
    del new_config_dict["csv_option"]

    with open("cblue_configuration.json", "w") as update_config:
        json.dump(new_config_dict, update_config, indent=4)
    if just_save_config:
        sys.exit()

if __name__ == "__main__":

    # Command Line Interface

    def get_help_text(options_list):
        """Generate command line interface help text for arguments that are designated using a list index value"""
        help_text = "Choose an integer. "
        for n, option in enumerate(options_list):
            option = option.replace("%", "%%")  # Escape percent sign to avoid argparse error
            help_text += f"{n}={option}, "
        help_text = help_text.strip(", ")
        return help_text

    # ADD ARGUMENTS
    parser = argparse.ArgumentParser(description="Run CBlueApp command line interface")
    # Data Directories
    parser.add_argument("in_sbet_dir", help="Trajectory directory file path.")
    parser.add_argument("in_las_dir", help="LAS directory file path.")
    parser.add_argument("output_dir", help="Output directory file path.")
    # Environmental Parameters
    # # Water Surface
    wind_values = [[1], [2, 3], [4, 5], [6, 7], [8, 9, 10]]
    wind_help_text = get_help_text(WIND_OPTIONS)
    parser.add_argument("wind", help=wind_help_text)
    # # Turbidity
    turbidity_values = [[6, 11], [11, 18], [18, 26], [26, 33], [33, 37]]
    turbidity_help_text = get_help_text(TURBIDITY_OPTIONS)
    parser.add_argument("turbidity", help=turbidity_help_text)
    # VDatum Region
    parser.add_argument("mcu", default=0.0, help=r"Input MCU value for the VDatum region. See .\lookup_tables\V_Datum_MCU_Values.txt for MCU values for different VDatum regions.")
    parser.add_argument("-vdatum_region", default=f"Used MCU value given in command", 
                        help=r"Adds the name of the VDatum region to the metadata log. User must provide region name after -vdatum_region flag.")
    # Sensor Model
    with open("lidar_sensors.json", "r") as sensors_json:
        sensor_json_content = json.load(sensors_json)
    sensor_options = list(sensor_json_content.keys())
    sensor_help_text = get_help_text(sensor_options)
    parser.add_argument("sensor", help=sensor_help_text)
    # TPU Metric
    tpu_help_text = get_help_text(TPU_METRIC_OPTIONS)
    parser.add_argument("tpu_metric", help=tpu_help_text)
    # Output Options
    parser.add_argument("--csv", action="store_true", help="Add the --csv flag to generate a CSV output files.")
    parser.add_argument("--just_save_config", action="store_true", help="Do not run process. Save config file only.")
    # Water Surface Ellipsoid Height
    parser.add_argument("water_height", help="Choose a number. Nominal water surface ellipsoid height")

    # RUN GUI IF NOT ARGUMENTS GIVEN
    if not len(sys.argv) > 1:
        subprocess.run(["python", "CBlueAppGui.py"])
        sys.exit()

    # PARSE ARGUMENTS
    args = parser.parse_args()
    in_sbet_dir = args.in_sbet_dir
    in_las_dir = args.in_las_dir
    output_dir = args.output_dir
    wind_index = int(args.wind)
    turbidity_index = int(args.turbidity)
    mcu = args.mcu
    vdatum_region = args.vdatum_region
    sensor_index = int(args.sensor)
    tpu_metric_index = int(args.tpu_metric)
    csv = args.csv
    just_save_config = args.just_save_config
    water_height = float(args.water_height)

    # UPDATE CONFIG
    with open("cblue_configuration.json", "r") as config:
        config_dict = json.load(config)
    config_dict["directories"] = {}
    config_dict["directories"]["sbet"] = in_sbet_dir
    config_dict["directories"]["las"] = in_las_dir
    config_dict["directories"]["tpu"] = output_dir
    config_dict["wind_ind"] = wind_index
    config_dict["wind_selection"] = WIND_OPTIONS[wind_index]
    config_dict["wind_vals"] = wind_values[wind_index]
    config_dict["kd_ind"] = turbidity_index
    config_dict["kd_selection"] = TURBIDITY_OPTIONS[turbidity_index]
    config_dict["kd_vals"] = (turbidity_values[turbidity_index][0], turbidity_values[turbidity_index][1])
    config_dict["vdatum_region"] = vdatum_region
    config_dict["mcu"] = mcu
    config_dict["sensor_model"] = sensor_options[sensor_index]
    config_dict["error_type"] = TPU_METRIC_OPTIONS[tpu_metric_index]
    config_dict["csv_option"] = csv
    config_dict["water_surface_ellipsoid_height"] = water_height

    updateConfig(config_dict)

    CBlueApp(config_dict)
